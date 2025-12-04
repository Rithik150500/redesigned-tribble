# agents/mcp_integration.py
"""
Integration layer for connecting MCP document analysis server to Deep Agents.

This module handles the connection between the agent system and the MCP server,
making the document analysis tools available to agents.
"""

import subprocess
import json
from typing import Optional
import os


class MCPServerConnection:
    """
    Manages connection to the MCP document analysis server.
    
    This class handles starting the MCP server process and communicating
    with it via JSON-RPC over stdin/stdout.
    """
    
    def __init__(self, server_path: str):
        """
        Initialize connection to MCP server.
        
        Args:
            server_path: Path to the MCP server Python script
        """
        self.server_path = server_path
        self.process = None
    
    def start(self):
        """Start the MCP server process."""
        if self.process is not None:
            return  # Already started
        
        self.process = subprocess.Popen(
            ['python', self.server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    
    def stop(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
        
        Returns:
            Tool execution result
        """
        if self.process is None:
            raise RuntimeError("MCP server not started")
        
        # Construct JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")
        
        response = json.loads(response_line)
        
        if "error" in response:
            raise RuntimeError(f"MCP server error: {response['error']}")
        
        return response.get("result", {})
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def create_mcp_tools(server_path: str):
    """
    Create tool wrappers that connect to the MCP server.
    
    These tools can be added to Deep Agents to give them access to
    the document analysis capabilities.
    
    Args:
        server_path: Path to the MCP server script
    
    Returns:
        List of tool functions
    """
    
    # In a full implementation, you would create wrapper functions here
    # that call the MCP server and return results in the format expected by agents
    # For brevity, this shows the pattern
    
    connection = MCPServerConnection(server_path)
    
    def list_documents() -> str:
        """List all available legal documents."""
        result = connection.call_tool("list_documents", {})
        # Extract text content from result
        if "content" in result:
            return result["content"][0]["text"]
        return str(result)
    
    def get_documents(doc_ids: list[int]) -> str:
        """Get detailed content for documents."""
        result = connection.call_tool("get_documents", {"doc_ids": doc_ids})
        if "content" in result:
            return result["content"][0]["text"]
        return str(result)
    
    def get_page_text(doc_id: int, page_nums: list[int]) -> str:
        """Get text content of specific pages."""
        result = connection.call_tool("get_page_text", {
            "doc_id": doc_id,
            "page_nums": page_nums
        })
        if "content" in result:
            return result["content"][0]["text"]
        return str(result)
    
    def get_page_image(doc_id: int, page_nums: list[int]) -> str:
        """Get page images (limited use)."""
        result = connection.call_tool("get_page_image", {
            "doc_id": doc_id,
            "page_nums": page_nums
        })
        if "content" in result:
            return result["content"][0]["text"]
        return str(result)
    
    return [list_documents, get_documents, get_page_text, get_page_image]
