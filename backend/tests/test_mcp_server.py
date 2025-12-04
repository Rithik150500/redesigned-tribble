# test_mcp_server.py
"""
Test script for the legal document analysis MCP server.

This script demonstrates how to interact with the MCP server programmatically.
It's useful for testing and debugging before integrating with agents.
"""

import subprocess
import json
import sys

def test_mcp_server():
    """
    Test the MCP server by sending tool invocation requests.
    
    This simulates what an MCP client (like a Deep Agent) would do when
    calling our tools.
    """
    print("Testing Legal Document Analysis MCP Server")
    print("=" * 60)
    
    # Start the MCP server as a subprocess
    # We'll communicate with it via stdin/stdout using JSON-RPC
    process = subprocess.Popen(
        ['python', 'legal_doc_mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    def send_request(method: str, params: dict = None):
        """Send a JSON-RPC request to the server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            return json.loads(response_line)
        return None
    
    try:
        # Test 1: List all documents
        print("\n1. Testing list_documents tool...")
        response = send_request("tools/call", {
            "name": "list_documents",
            "arguments": {}
        })
        
        if response and "result" in response:
            print("✓ Success! Response:")
            # The actual content will be in the content array
            if "content" in response["result"]:
                for item in response["result"]["content"]:
                    if item["type"] == "text":
                        print(item["text"][:500] + "...\n")
        else:
            print("✗ Failed to list documents")
            print(response)
        
        # Test 2: Get a specific document (assuming doc_id 1 exists)
        print("\n2. Testing get_documents tool...")
        response = send_request("tools/call", {
            "name": "get_documents",
            "arguments": {"doc_ids": [1]}
        })
        
        if response and "result" in response:
            print("✓ Success! Retrieved document 1")
            if "content" in response["result"]:
                for item in response["result"]["content"]:
                    if item["type"] == "text":
                        print(item["text"][:500] + "...\n")
        else:
            print("✗ Failed to get document")
            print(response)
        
        # Test 3: Get specific page text
        print("\n3. Testing get_page_text tool...")
        response = send_request("tools/call", {
            "name": "get_page_text",
            "arguments": {"doc_id": 1, "page_nums": [1, 2]}
        })
        
        if response and "result" in response:
            print("✓ Success! Retrieved page text")
        else:
            print("✗ Failed to get page text")
            print(response)
        
        print("\n" + "=" * 60)
        print("Testing complete!")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    # Make sure you've processed some documents first
    print("\nNote: This test assumes you have already run ingest_documents.py")
    print("and have at least one document in your database.\n")
    
    response = input("Have you processed documents? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        test_mcp_server()
    else:
        print("\nPlease run ingest_documents.py first to populate the database.")
        print("Then run this test script again.")
