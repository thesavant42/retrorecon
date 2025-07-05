import os
import sqlite3
import logging
import json
import datetime
from typing import Dict, Any, List, Optional
import anyio
from mcp.server.fastmcp import FastMCP
from mcp import types
import httpx
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..windows_tz import to_iana
from .config import MCPConfig, load_config

logger = logging.getLogger(__name__)


class RetroReconMCPServer:
    """Embedded MCP server for querying RetroRecon SQLite databases."""

    def __init__(self, db_path: Optional[str] = None, config: MCPConfig | None = None) -> None:
        self.config = config or load_config()
        self.db_path = db_path or self.config.db_path
        self.api_base = self.config.api_base
        self.model = self.config.model
        self.temperature = self.config.temperature
        self.row_limit = self.config.row_limit
        self.api_key = self.config.api_key
        self.timeout = self.config.timeout
        self.server = FastMCP("RetroRecon SQLite Explorer")
        self._setup_tools()
        logger.debug(
            "MCPServer init db=%s api_base=%s model=%s row_limit=%d",
            self.db_path,
            self.api_base,
            self.model,
            self.row_limit,
        )


    def _llm_chat(self, message: str) -> tuple[str, list[dict[str, Any]]]:
        """Send *message* to the configured model and return the reply along with tool logs."""
        if not self.api_base:
            raise RuntimeError("API base not configured")
        url = f"{self.api_base}/chat/completions"
        api_bases = [self.api_base] + list(self.config.alt_api_bases or [])
        base_idx = 0
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": message},
            ],
            "temperature": self.temperature,
            "tools": self._openai_tools(),
            "tool_choice": "auto",
        }
        logger.debug("LLM payload: %s", json.dumps(payload))
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        tool_logs: list[dict[str, Any]] = []

        while True:
            try:
                resp = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
            except Exception as exc:
                logger.error("LLM request failed via %s: %s", url, exc)
                base_idx += 1
                if base_idx >= len(api_bases):
                    raise
                url = f"{api_bases[base_idx]}/chat/completions"
                logger.debug("retrying LLM request via %s", url)
                continue
            data = resp.json()
            logger.debug("LLM response: %s", json.dumps(data))
            try:
                message_data = data["choices"][0]["message"]
            except Exception as exc:  # pragma: no cover - handle unexpected schema
                logger.error("Invalid LLM response: %s", exc)
                raise RuntimeError("Invalid LLM response")

            if not message_data.get("tool_calls"):
                break

            tool_msgs: list[dict[str, Any]] = []
            for call in message_data["tool_calls"]:
                name = call["function"]["name"]
                try:
                    args = json.loads(call["function"].get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                result = self._call_tool(name, args)
                tool_logs.append({"name": name, "args": args, "result": result})
                tool_msgs.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result),
                })

            payload["messages"].append(message_data)
            payload["messages"].extend(tool_msgs)

        return message_data.get("content", "").strip(), tool_logs

    # tool setup
    def _setup_tools(self) -> None:
        logger.debug(
            "initializing tools db=%s model=%s",
            self.db_path,
            self.model,
        )
        self.server.add_tool(self._create_read_query_tool())
        self.server.add_tool(self._create_list_tables_tool())
        self.server.add_tool(self._create_describe_table_tool())
        self.server.add_tool(self._create_time_now_tool())
        logger.debug("MCP tools registered")

    def update_database_path(self, db_path: str) -> None:
        self.db_path = db_path
        self.config.db_path = db_path
        logger.debug("database path updated: %s", db_path)

    def _openai_tools(self) -> list[dict[str, Any]]:
        """Return tool specifications for OpenAI tool calling."""
        try:
            list_fn = getattr(self.server, "_list_tools", None)
            if list_fn is None:
                list_fn = getattr(self.server, "list_tools")
            tools = anyio.run(list_fn)
        except Exception as exc:  # pragma: no cover - log and continue
            logger.error("Failed to list tools: %s", exc)
            tools = []

        specs: list[dict[str, Any]] = []
        for tool in tools:
            params = getattr(tool, "parameters", {"type": "object", "properties": {}})
            try:
                name = getattr(tool, "key")
            except AttributeError:
                name = getattr(tool, "name", getattr(tool, "__name__", ""))
            description = getattr(tool, "description", "")
            specs.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": params,
                    },
                }
            )
        return specs

    def _call_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any] | str:
        """Execute a tool by name and return its result as a JSON-able object."""
        logger.debug("call tool %s args=%s", name, args)
        if name == "read_query":
            query = args.get("query", "")
            params = args.get("params")
            content = anyio.run(self.handle_read_query, query, params)
            return {"type": "text", "text": content.text}
        if name == "list_tables":
            content = anyio.run(self.handle_list_tables)
            return {"type": "text", "text": content.text}
        if name == "describe_table":
            table = args.get("table", "")
            content = anyio.run(self.handle_describe_table, table)
            return {"type": "text", "text": content.text}
        if name.startswith("time"):
            tz_name = args.get("timezone")
            mapped = to_iana(tz_name) if tz_name else None
            if mapped:
                args["timezone"] = mapped
        async def _run_call():
            from fastmcp.server.context import Context
            async with Context(self.server):
                return await self.server.call_tool(name, args)

        try:
            result = anyio.run(_run_call)
            if result.structured_content:
                logger.debug("tool %s returned structured", name)
                return result.structured_content
            if result.content:
                blocks = [getattr(b, "text", str(b)) for b in result.content]
                logger.debug("tool %s returned text", name)
                return {"type": "text", "text": "\n".join(blocks)}
        except Exception as exc:
            logger.error("External tool failed: %s", exc)
            if name.startswith("time"):
                tz_name = args.get("timezone", "UTC")
                mapped = to_iana(tz_name)
                if mapped:
                    tz_name = mapped
                try:
                    tz = ZoneInfo(tz_name)
                except ZoneInfoNotFoundError:
                    tz = ZoneInfo("UTC")
                now = datetime.datetime.now(tz)
                logger.debug("time fallback timezone=%s", tz.key)
                return {"type": "text", "text": now.strftime("%Y-%m-%d %H:%M:%S %Z")}
            return {"error": str(exc)}
        logger.error("Unknown tool requested: %s", name)
        return {"error": f"Unknown tool: {name}"}

    # tools
    def _create_read_query_tool(self):
        async def read_query(query: str, params: list[Any] | None = None) -> types.TextContent:
            return await self.handle_read_query(query, params)

        return read_query

    def _create_list_tables_tool(self):
        async def list_tables() -> types.TextContent:
            return await self.handle_list_tables()

        return list_tables

    def _create_describe_table_tool(self):
        async def describe_table(table: str) -> types.TextContent:
            return await self.handle_describe_table(table)

        return describe_table

    def _create_time_now_tool(self):
        async def time_now(timezone: str | None = None) -> types.TextContent:
            tz_name = timezone or "UTC"
            mapped = to_iana(tz_name) if tz_name else None
            if mapped:
                tz_name = mapped
            try:
                tz = ZoneInfo(tz_name)
            except ZoneInfoNotFoundError:
                tz = ZoneInfo("UTC")
            now = datetime.datetime.now(tz)
            return types.TextContent(type="text", text=now.strftime("%Y-%m-%d %H:%M:%S %Z"))

        return time_now

    # connection helpers
    def get_connection(self):
        if not self.db_path:
            raise ValueError("Database path not configured")
        logger.debug("opening sqlite connection to %s", self.db_path)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # validation
    def validate_query(self, query: str) -> bool:
        query_upper = query.upper().strip()
        logger.debug("validate query: %s", query_upper)
        if not query_upper.startswith("SELECT"):
            return False
        prohibited = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]
        return not any(k in query_upper for k in prohibited)

    # query execution
    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a validated SELECT statement."""
        if not self.validate_query(query):
            raise ValueError("Query validation failed")
        logger.debug("execute query: %s params=%s", query, params)
        with self.get_connection() as conn:
            c = conn.cursor()
            if "LIMIT" not in query.upper():
                query += f" LIMIT {self.row_limit}"
            c.execute(query, params or [])
            rows = c.fetchall()
            columns = [d[0] for d in c.description]
            logger.debug("query returned %d rows", len(rows))
            return {"columns": columns, "rows": rows, "count": len(rows)}

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Return a response for a natural language chat question.

        The chat interface accepts **only** plain English questions. Even if a
        valid SQL statement is provided, it will **not** be executed directly.
        This avoids exposing raw query execution through the chat bar while
        preserving helpful feedback for casual greetings or unsupported input.
        """
        lowered = question.strip().lower()
        if self.validate_query(question):
            return {
                "error": "Direct SQL input is not supported in chat",
                "hint": "Ask your question in plain English instead",
            }

        if lowered in {"hello", "hi"}:
            return {"message": "Hello! Ask me a database question."}
        if lowered in {"help", "?"}:
            db_info = self.db_path if self.db_path else "(no database loaded)"
            return {
                "message": (
                    "RetroRecon chat is ready. "
                    f"Database: {db_info}. Model: {self.model}. "
                    "Ask about your data in plain English."
                )
            }
        if lowered == "prompt":
            return {"message": "Try asking about tables or data in plain English."}

        try:
            logger.debug("chat question: %s", question)
            reply, tools = self._llm_chat(question)
            logger.debug("chat reply: %s", reply)
            resp = {"message": reply}
            if tools:
                resp["tools"] = tools
            return resp
        except Exception as exc:
            logger.error("LLM request failed: %s", exc)
            return {
                "error": "LLM request failed",
                "hint": str(exc),
            }

    # handlers
    async def handle_read_query(self, query: str, params: Optional[List[Any]] = None) -> types.TextContent:
        logger.debug("handle_read_query %s", query)
        try:
            results = self.execute_query(query, params)
            if results["count"] == 0:
                return types.TextContent(type="text", text="No results found for the query.")
            formatted = self._format_query_results(results)
            return types.TextContent(type="text", text=formatted)
        except Exception as exc:
            logger.error("Query execution failed: %s", exc)
            return types.TextContent(type="text", text=f"Query execution failed: {exc}")

    async def handle_list_tables(self) -> types.TextContent:
        logger.debug("handle_list_tables")
        try:
            q = "SELECT name FROM sqlite_master WHERE type='table'"
            results = self.execute_query(q)
            tables = [r[0] for r in results["rows"]]
            return types.TextContent(type="text", text="\n".join(tables))
        except Exception as exc:
            logger.error("List tables failed: %s", exc)
            return types.TextContent(type="text", text=f"Failed to list tables: {exc}")

    async def handle_describe_table(self, table: str) -> types.TextContent:
        logger.debug("handle_describe_table %s", table)
        try:
            q = f"PRAGMA table_info({table})"
            results = self.execute_query(q)
            return types.TextContent(type="text", text=self._format_query_results(results))
        except Exception as exc:
            logger.error("Describe table failed: %s", exc)
            return types.TextContent(type="text", text=f"Failed to describe table: {exc}")

    # formatting helper
    def _format_query_results(self, results: Dict[str, Any]) -> str:
        header = " | ".join(results["columns"])
        separator = " | ".join("-" * len(c) for c in results["columns"])
        rows = [
            " | ".join(str(cell) if cell is not None else "" for cell in row)
            for row in results["rows"]
        ]
        return "{}\n{}\n{}".format(header, separator, "\n".join(rows))

    def cleanup(self) -> None:
        logger.debug("MCP server cleanup")
        pass
