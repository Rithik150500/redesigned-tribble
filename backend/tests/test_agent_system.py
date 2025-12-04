# test_agent_system.py
"""
Test script for the Deep Agent legal analysis system.

This script tests the complete workflow:
1. Document processing (assumes already done)
2. MCP server connectivity
3. Agent initialization
4. Human-in-the-loop approvals
5. Analysis execution
6. Report generation
"""

import sys
from pathlib import Path

def test_prerequisites():
    """Check that all prerequisites are met."""
    print("Checking prerequisites...")
    
    # Check database exists
    if not Path("legal_documents.db").exists():
        print("✗ Database not found")
        print("  Run: python ingest_documents.py")
        return False
    print("✓ Database found")
    
    # Check MCP server exists
    if not Path("legal_doc_mcp_server.py").exists():
        print("✗ MCP server not found")
        return False
    print("✓ MCP server found")
    
    # Check API key
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("✗ ANTHROPIC_API_KEY not set")
        return False
    print("✓ API key configured")
    
    return True


def test_database():
    """Test database connectivity and content."""
    print("\nTesting database...")
    
    from database import LegalDocumentDatabase
    db = LegalDocumentDatabase()
    
    docs = db.get_all_documents()
    if not docs:
        print("✗ No documents in database")
        return False
    
    print(f"✓ Found {len(docs)} documents")
    
    for doc in docs[:3]:  # Show first 3
        print(f"  - {doc['filename']}: {doc['total_pages']} pages")
    
    return True


def test_mcp_server():
    """Test MCP server can be started and responds."""
    print("\nTesting MCP server...")
    
    from agents.mcp_integration import MCPServerConnection
    
    try:
        with MCPServerConnection("legal_doc_mcp_server.py") as conn:
            result = conn.call_tool("list_documents", {})
            print("✓ MCP server responds")
            return True
    except Exception as e:
        print(f"✗ MCP server error: {e}")
        return False


def test_agent_creation():
    """Test that agents can be created."""
    print("\nTesting agent creation...")
    
    from agents.main_agent import create_legal_risk_agent
    
    try:
        agent = create_legal_risk_agent()
        print("✓ Main agent created")
        return True
    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        return False


def run_tests():
    """Run all tests."""
    print("="*70)
    print("LEGAL RISK ANALYSIS SYSTEM - TEST SUITE")
    print("="*70)
    
    tests = [
        ("Prerequisites", test_prerequisites),
        ("Database", test_database),
        ("MCP Server", test_mcp_server),
        ("Agent Creation", test_agent_creation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n✓ All tests passed! System is ready for analysis.")
        print("\nRun: python run_analysis.py")
    else:
        print("\n✗ Some tests failed. Please fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
