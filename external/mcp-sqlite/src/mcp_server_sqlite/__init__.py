from . import server
import asyncio
import argparse


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='SQLite MCP Server')
    parser.add_argument('--db-path', 
                       default="./sqlite_mcp_server.db",
                       help='Path to SQLite database file')
    
    args = parser.parse_args()
    try:
        asyncio.run(server.main(args.db_path))
    except KeyboardInterrupt:
        server.logger.info("SQLite MCP Server interrupted")


# Optionally expose other important items at package level
__all__ = ["main", "server"]
