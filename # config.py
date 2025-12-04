# config.py
"""
Configuration for the legal document analysis MCP server.

This module provides configuration management for connecting the MCP server
to various hosts and managing operational parameters.
"""

import os
from pathlib import Path

# Database configuration
DATABASE_PATH = os.getenv("LEGAL_DOC_DB_PATH", "legal_documents.db")

# API keys (for future use if we add additional capabilities)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Server configuration
SERVER_NAME = "legal-document-analysis"
SERVER_VERSION = "1.0.0"

# Tool usage limits (for future implementation of usage tracking)
MAX_IMAGE_REQUESTS_PER_SESSION = 10
MAX_PAGES_PER_IMAGE_REQUEST = 5

def get_mcp_config():
    """
    Generate MCP server configuration for various hosts.
    
    This returns configuration in the format expected by MCP hosts
    like Claude Desktop.
    """
    return {
        "mcpServers": {
            SERVER_NAME: {
                "command": "python",
                "args": [
                    str(Path(__file__).parent / "legal_doc_mcp_server.py")
                ],
                "env": {
                    "LEGAL_DOC_DB_PATH": DATABASE_PATH
                }
            }
        }
    }

def print_claude_desktop_config():
    """
    Print configuration instructions for Claude Desktop.
    
    Users can copy this to their Claude Desktop configuration file.
    """
    config = get_mcp_config()["mcpServers"][SERVER_NAME]
    
    # Get absolute path for the configuration
    server_path = Path(__file__).parent / "legal_doc_mcp_server.py"
    
    print("\n" + "="*70)
    print("CLAUDE DESKTOP CONFIGURATION")
    print("="*70)
    print("\nAdd this to your claude_desktop_config.json file:")
    print("\n{")
    print('  "mcpServers": {')
    print(f'    "{SERVER_NAME}": {{')
    print(f'      "command": "python",')
    print(f'      "args": ["{server_path.absolute()}"]')
    print('    }')
    print('  }')
    print("}\n")
    print("Location of config file:")
    print("  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("  Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    print_claude_desktop_config()
