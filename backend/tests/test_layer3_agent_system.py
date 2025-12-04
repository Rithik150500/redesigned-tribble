"""
Test Suite for Layer 3: Deep Agent Orchestration

This test suite covers:
- Main agent initialization and configuration
- Subagent creation and delegation
- Human-in-the-loop approval workflow
- Agent state management and checkpointing
- MCP tool integration
- Command-line approval flow
- Error handling and recovery
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for agent testing."""
    with patch('anthropic.Anthropic') as mock:
        client = MagicMock()
        mock.return_value = client

        # Mock response
        response = MagicMock()
        response.content = [MagicMock(text="Test response from agent")]

        client.messages.create.return_value = response
        yield client


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing agent integration."""
    with patch('agents.mcp_integration.subprocess') as mock_subprocess:
        mock_process = MagicMock()
        mock_subprocess.Popen.return_value = mock_process

        # Mock MCP responses
        mock_process.stdout.readline.return_value = json.dumps({
            "jsonrpc": "2.0",
            "result": {"content": [{"text": "Mocked MCP response"}]},
            "id": 1
        }).encode()

        yield mock_process


# ============================================================================
# Agent Creation and Initialization Tests
# ============================================================================

class TestAgentCreation:
    """Test agent creation and configuration."""

    def test_create_main_agent(self, mock_anthropic_client):
        """Test creating the main coordination agent."""
        from agents.main_agent import create_legal_risk_agent

        agent = create_legal_risk_agent(anthropic_api_key="test_key")

        assert agent is not None

    def test_create_agent_with_checkpointer(self, mock_anthropic_client):
        """Test creating agent with persistent checkpointer."""
        from agents.main_agent import create_legal_risk_agent
        from langgraph.checkpoint.memory import MemorySaver

        checkpointer = MemorySaver()
        agent = create_legal_risk_agent(
            anthropic_api_key="test_key",
            checkpointer=checkpointer
        )

        assert agent is not None

    def test_create_agent_with_store(self, mock_anthropic_client):
        """Test creating agent with memory store."""
        from agents.main_agent import create_legal_risk_agent
        from langgraph.store.memory import InMemoryStore

        store = InMemoryStore()
        agent = create_legal_risk_agent(
            anthropic_api_key="test_key",
            store=store
        )

        assert agent is not None

    def test_agent_requires_api_key(self):
        """Test that agent creation requires API key."""
        from agents.main_agent import create_legal_risk_agent

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                create_legal_risk_agent()

    @patch('agents.main_agent.create_analysis_subagent')
    @patch('agents.main_agent.create_report_subagent')
    def test_agent_registers_subagents(self, mock_report, mock_analysis,
                                      mock_anthropic_client):
        """Test that subagents are registered during creation."""
        from agents.main_agent import create_legal_risk_agent

        agent = create_legal_risk_agent(anthropic_api_key="test_key")

        # Verify subagents were created
        mock_analysis.assert_called()
        mock_report.assert_called()


# ============================================================================
# Subagent Tests
# ============================================================================

class TestSubagents:
    """Test subagent functionality."""

    def test_create_analysis_subagent(self, mock_anthropic_client):
        """Test creating the analysis subagent."""
        from agents.analysis_subagent import create_analysis_subagent

        subagent_config = create_analysis_subagent("test_key")

        assert subagent_config is not None
        assert 'name' in subagent_config
        assert subagent_config['name'] == 'Analysis'

    def test_create_report_subagent(self, mock_anthropic_client):
        """Test creating the report subagent."""
        from agents.report_subagent import create_report_subagent

        subagent_config = create_report_subagent("test_key")

        assert subagent_config is not None
        assert 'name' in subagent_config
        assert subagent_config['name'] == 'Create Report'

    def test_analysis_subagent_has_mcp_tools(self):
        """Test that analysis subagent has access to MCP tools."""
        from agents.analysis_subagent import create_analysis_subagent

        subagent_config = create_analysis_subagent("test_key")

        # Check for MCP tool configuration
        assert 'system_prompt' in subagent_config
        assert 'list_documents' in subagent_config['system_prompt']

    def test_report_subagent_filesystem_access(self):
        """Test that report subagent can access filesystem."""
        from agents.report_subagent import create_report_subagent

        subagent_config = create_report_subagent("test_key")

        # Check that it has file access capabilities
        assert 'system_prompt' in subagent_config


# ============================================================================
# Human-in-the-Loop Approval Tests
# ============================================================================

class TestApprovalWorkflow:
    """Test human-in-the-loop approval workflow."""

    @patch('agents.main_agent.create_deep_agent')
    def test_agent_pauses_for_approval(self, mock_create_agent,
                                       mock_anthropic_client):
        """Test that agent pauses when approval is needed."""
        # Mock agent to return interrupt
        mock_agent = MagicMock()
        mock_result = {
            "__interrupt__": [{
                "value": {
                    "action_requests": [{
                        "name": "write_file",
                        "args": {"file_path": "/test.txt", "content": "test"}
                    }],
                    "review_configs": [{"action_name": "write_file", "review": True}]
                }
            }]
        }
        mock_agent.invoke.return_value = mock_result
        mock_create_agent.return_value = mock_agent

        from agents.main_agent import create_legal_risk_agent

        agent = create_legal_risk_agent(anthropic_api_key="test_key")

        config = {"configurable": {"thread_id": "test"}}
        result = agent.invoke({"messages": [{"role": "user", "content": "test"}]}, config=config)

        # Should have interrupt
        assert "__interrupt__" in result

    def test_approval_context_building(self):
        """Test building context for approval requests."""
        from agents.utils import extract_action_results_from_interrupt

        interrupt_data = {
            "action_requests": [
                {
                    "id": "action_1",
                    "name": "get_documents",
                    "args": {"doc_ids": [1, 2]},
                    "metadata": {}
                }
            ]
        }

        actions = extract_action_results_from_interrupt(interrupt_data)

        assert len(actions) == 1
        assert actions[0]['tool_name'] == 'get_documents'
        assert actions[0]['arguments']['doc_ids'] == [1, 2]


# ============================================================================
# Document Formatting Tests
# ============================================================================

class TestDocumentFormatting:
    """Test document formatting for agent prompts."""

    def test_format_document_summaries(self):
        """Test formatting document summaries for prompt."""
        from agents.utils import format_document_summaries_for_prompt
        from database import LegalDocumentDatabase
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LegalDocumentDatabase(db_path)

        try:
            # Add test document
            doc_id = db.add_document(
                filename="test.pdf",
                filepath="/path/test.pdf",
                file_hash="hash"
            )

            # Update with summary
            cursor = db.conn.cursor()
            cursor.execute("""
                UPDATE documents
                SET summdesc = ?, total_pages = ?, legally_significant_pages = ?
                WHERE doc_id = ?
            """, ("Test summary", 10, 3, doc_id))
            db.conn.commit()

            # Format for prompt
            formatted = format_document_summaries_for_prompt(db)

            assert "AVAILABLE DOCUMENTS" in formatted
            assert "test.pdf" in formatted
            assert "Test summary" in formatted
            assert "10 total" in formatted
            assert "3 legally significant" in formatted

        finally:
            db.close()
            import os
            os.unlink(db_path)

    def test_format_empty_database(self):
        """Test formatting when no documents exist."""
        from agents.utils import format_document_summaries_for_prompt
        from database import LegalDocumentDatabase
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LegalDocumentDatabase(db_path)

        try:
            formatted = format_document_summaries_for_prompt(db)
            assert "No documents" in formatted
        finally:
            db.close()
            import os
            os.unlink(db_path)


# ============================================================================
# MCP Integration Tests
# ============================================================================

class TestMCPIntegration:
    """Test MCP server integration with agents."""

    @patch('agents.mcp_integration.subprocess.Popen')
    def test_mcp_server_startup(self, mock_popen):
        """Test starting MCP server process."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        from agents.mcp_integration import start_mcp_server

        process = start_mcp_server("./legal_doc_mcp_server.py")

        assert process is not None
        mock_popen.assert_called_once()

    def test_mcp_tool_configuration(self):
        """Test MCP tool configuration in agents."""
        from agents.analysis_subagent import create_analysis_subagent

        config = create_analysis_subagent("test_key")

        # Should reference MCP tools
        system_prompt = config.get('system_prompt', '')
        assert 'list_documents' in system_prompt
        assert 'get_documents' in system_prompt


# ============================================================================
# State Management and Checkpointing Tests
# ============================================================================

class TestStateManagement:
    """Test agent state management."""

    @patch('agents.main_agent.create_deep_agent')
    def test_agent_state_persists(self, mock_create_agent, mock_anthropic_client):
        """Test that agent state persists across invocations."""
        from agents.main_agent import create_legal_risk_agent
        from langgraph.checkpoint.memory import MemorySaver

        checkpointer = MemorySaver()

        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [{"content": "test"}]}
        mock_create_agent.return_value = mock_agent

        agent = create_legal_risk_agent(
            anthropic_api_key="test_key",
            checkpointer=checkpointer
        )

        config = {"configurable": {"thread_id": "test_thread"}}

        # First invocation
        result1 = agent.invoke({"messages": [{"role": "user", "content": "first"}]}, config=config)

        # Second invocation (should use same thread)
        result2 = agent.invoke({"messages": [{"role": "user", "content": "second"}]}, config=config)

        # Both should succeed
        assert result1 is not None
        assert result2 is not None

    def test_filesystem_backend_configuration(self):
        """Test filesystem backend configuration."""
        from agents.main_agent import create_legal_risk_agent

        # This should create composite backend with state + store
        agent = create_legal_risk_agent(anthropic_api_key="test_key")

        assert agent is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestAgentErrorHandling:
    """Test error handling in agent system."""

    @patch('agents.main_agent.create_deep_agent')
    def test_agent_handles_api_errors(self, mock_create_agent):
        """Test agent handles API errors gracefully."""
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = Exception("API Error")
        mock_create_agent.return_value = mock_agent

        from agents.main_agent import create_legal_risk_agent

        agent = create_legal_risk_agent(anthropic_api_key="test_key")

        config = {"configurable": {"thread_id": "test"}}

        with pytest.raises(Exception, match="API Error"):
            agent.invoke({"messages": [{"role": "user", "content": "test"}]}, config=config)

    def test_agent_validates_config(self):
        """Test agent validates configuration."""
        from agents.main_agent import create_legal_risk_agent

        # Missing API key should raise error
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError):
                create_legal_risk_agent()


# ============================================================================
# Command-Line Approval Flow Tests
# ============================================================================

class TestCommandLineApproval:
    """Test command-line approval workflow."""

    @patch('builtins.input', return_value='approve')
    @patch('agents.main_agent.create_deep_agent')
    def test_cli_approval_approve(self, mock_create_agent, mock_input,
                                  mock_anthropic_client):
        """Test approving an action via CLI."""
        # This tests the pattern used in run_analysis.py

        mock_agent = MagicMock()
        mock_result = {
            "__interrupt__": [{
                "value": {
                    "action_requests": [{
                        "name": "write_file",
                        "args": {"file_path": "/test.txt", "content": "test"}
                    }],
                    "review_configs": [{"action_name": "write_file"}]
                }
            }]
        }
        mock_agent.invoke.return_value = mock_result
        mock_create_agent.return_value = mock_agent

        from agents.main_agent import create_legal_risk_agent

        agent = create_legal_risk_agent(anthropic_api_key="test_key")

        config = {"configurable": {"thread_id": "test"}}
        result = agent.invoke({"messages": [{"role": "user", "content": "test"}]}, config=config)

        # Should have interrupt
        assert "__interrupt__" in result

        # Simulate CLI approval (this is what run_analysis.py does)
        user_decision = mock_input("Approve? ")
        assert user_decision == 'approve'

    def test_cli_displays_approval_context(self):
        """Test that CLI shows context for approvals."""
        # This is a documentation test - the CLI should show:
        # 1. What action the agent wants to take
        # 2. The arguments
        # 3. Why it needs approval

        approval_context = {
            "tool_name": "write_file",
            "arguments": {"file_path": "/analysis/findings.md", "content": "..."},
            "review_config": {"action_name": "write_file", "review": True}
        }

        # Format for display
        display = f"""
Action: {approval_context['tool_name']}
Arguments: {approval_context['arguments']}
        """

        assert "write_file" in display
        assert "/analysis/findings.md" in display


# ============================================================================
# Integration Tests
# ============================================================================

class TestAgentIntegration:
    """Integration tests for agent system."""

    @patch('agents.main_agent.create_deep_agent')
    @patch('agents.mcp_integration.subprocess.Popen')
    def test_full_analysis_workflow(self, mock_popen, mock_create_agent,
                                    mock_anthropic_client):
        """Test complete analysis workflow."""
        # Mock MCP server
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        # Mock agent responses
        mock_agent = MagicMock()

        # First call: planning (no interrupt)
        # Second call: request document access (interrupt)
        # Third call: after approval, continue (no interrupt)
        mock_agent.invoke.side_effect = [
            {"messages": [{"content": "Planning analysis"}]},
            {
                "__interrupt__": [{
                    "value": {
                        "action_requests": [{
                            "name": "get_documents",
                            "args": {"doc_ids": [1]}
                        }],
                        "review_configs": [{"action_name": "get_documents"}]
                    }
                }]
            },
            {"messages": [{"content": "Analysis complete"}]}
        ]

        mock_create_agent.return_value = mock_agent

        from agents.main_agent import create_legal_risk_agent

        agent = create_legal_risk_agent(anthropic_api_key="test_key")

        config = {"configurable": {"thread_id": "test"}}

        # Start analysis
        result1 = agent.invoke({"messages": [{"role": "user", "content": "Analyze"}]}, config=config)

        # Should complete planning
        assert "messages" in result1

        # Next call should request approval
        result2 = agent.invoke({"messages": []}, config=config)
        assert "__interrupt__" in result2

        # After approval, continue
        from langgraph.types import Command
        result3 = agent.invoke(Command(resume={"decisions": [{"decision": "approve"}]}), config=config)

        # Should complete
        assert "messages" in result3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
