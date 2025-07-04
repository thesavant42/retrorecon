import os
import sqlite3
import logging
import json
from typing import Dict, Any, List, Optional

from fastmcp import FastMCP
from mcp.types import TextContent
import httpx
try:
    from fastmcp.tools import FunctionTool
except Exception:  # pragma: no cover - fallback for older fastmcp
    class FunctionTool:
        """Minimal stub when fastmcp lacks FunctionTool."""

        @staticmethod
        def from_function(func, name=None, description=None):
            return func
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

    def _llm_chat(self, message: str) -> str:
        """Send *message* to the configured model and return the reply."""
        if not self.api_base:
            raise RuntimeError("API base not configured")
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": message},
            ],
            "temperature": self.temperature,
        }
        logger.debug("LLM payload: %s", json.dumps(payload))
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        resp = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # pragma: no cover - handle unexpected schema
            logger.error("Invalid LLM response: %s", exc)
            raise RuntimeError("Invalid LLM response")

    # tool setup
    def _setup_tools(self) -> None:
        self.server.add_tool(self._create_read_query_tool())
        self.server.add_tool(self._create_list_tables_tool())
        self.server.add_tool(self._create_describe_table_tool())

    def update_database_path(self, db_path: str) -> None:
        self.db_path = db_path
        self.config.db_path = db_path

    # tools
    def _create_read_query_tool(self):
        async def read_query(query: str, params: list[Any] | None = None) -> TextContent:
            return await self.handle_read_query(query, params)

        return FunctionTool.from_function(
            read_query,
            name="read_query",
            description="Execute a SELECT query on the RetroRecon database",
        )

    def _create_list_tables_tool(self):
        async def list_tables() -> TextContent:
            return await self.handle_list_tables()

        return FunctionTool.from_function(
            list_tables,
            name="list_tables",
            description="List tables in the current database",
        )

    def _create_describe_table_tool(self):
        async def describe_table(table: str) -> TextContent:
            return await self.handle_describe_table(table)

        return FunctionTool.from_function(
            describe_table,
            name="describe_table",
            description="Describe table columns",
        )

    # connection helpers
    def get_connection(self):
        if not self.db_path:
            raise ValueError("Database path not configured")
        return sqlite3.connect(self.db_path)

    # validation
    def validate_query(self, query: str) -> bool:
        query_upper = query.upper().strip()
        if not query_upper.startswith("SELECT"):
            return False
        prohibited = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]
        return not any(k in query_upper for k in prohibited)

    # query execution
    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a validated SELECT statement."""
        if not self.validate_query(query):
            raise ValueError("Query validation failed")
        with self.get_connection() as conn:
            c = conn.cursor()
            if "LIMIT" not in query.upper():
                query += f" LIMIT {self.row_limit}"
            c.execute(query, params or [])
            rows = c.fetchall()
            columns = [d[0] for d in c.description]
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
            reply = self._llm_chat(question)
            return {"message": reply}
        except Exception as exc:
            logger.error("LLM request failed: %s", exc)
            return {
                "error": "LLM request failed",
                "hint": str(exc),
            }

    # handlers
    async def handle_read_query(self, query: str, params: Optional[List[Any]] = None) -> TextContent:
        try:
            results = self.execute_query(query, params)
            if results["count"] == 0:
                return TextContent(text="No results found for the query.")
            formatted = self._format_query_results(results)
            return TextContent(text=formatted)
        except Exception as exc:
            logger.error("Query execution failed: %s", exc)
            return TextContent(text=f"Query execution failed: {exc}")

    async def handle_list_tables(self) -> TextContent:
        try:
            q = "SELECT name FROM sqlite_master WHERE type='table'"
            results = self.execute_query(q)
            tables = [r[0] for r in results["rows"]]
            return TextContent(text="\n".join(tables))
        except Exception as exc:
            logger.error("List tables failed: %s", exc)
            return TextContent(text=f"Failed to list tables: {exc}")

    async def handle_describe_table(self, table: str) -> TextContent:
        try:
            q = f"PRAGMA table_info({table})"
            results = self.execute_query(q)
            return TextContent(text=self._format_query_results(results))
        except Exception as exc:
            logger.error("Describe table failed: %s", exc)
            return TextContent(text=f"Failed to describe table: {exc}")

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
        pass
