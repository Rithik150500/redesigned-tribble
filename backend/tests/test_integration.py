"""
Integration Tests: End-to-End Testing Across All Layers

This test suite covers:
- Full pipeline from PDF ingestion to agent analysis
- Cross-layer integration
- Complete workflow simulation
- Performance under realistic conditions
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import LegalDocumentDatabase
from document_processor import DocumentProcessor


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
def integration_db(tmp_path):
    """Create database for integration testing."""
    db_path = tmp_path / "integration_test.db"
    db = LegalDocumentDatabase(str(db_path))
    yield db
    db.close()


@pytest.fixture
def mock_pdf_content():
    """Mock PDF content for testing."""
    return b"%PDF-1.4\nFake PDF content for testing"


# ============================================================================
# Layer 1 → Layer 2 Integration
# ============================================================================

class TestLayer1ToLayer2Integration:
    """Test document processing → MCP server integration."""

    @patch('document_processor.convert_from_path')
    @patch('document_processor.pypdf.PdfReader')
    @patch('document_processor.anthropic.Anthropic')
    def test_ingest_document_then_access_via_mcp(
        self, mock_anthropic, mock_pdf_reader, mock_convert,
        integration_db, tmp_path
    ):
        """Test: Ingest document → Access via MCP tools."""

        # Setup mocks for document processing
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Mock page summarization
        page_response = MagicMock()
        page_response.content = [MagicMock(text="Page summary")]

        # Mock document analysis
        doc_response = MagicMock()
        doc_response.content = [MagicMock(text="""SUMMARY: Test document summary
SIGNIFICANT_PAGES: 1,3""")]

        mock_client.messages.create.side_effect = [
            page_response, page_response, page_response, doc_response
        ]

        # Mock PDF reader
        mock_pages = [MagicMock() for _ in range(3)]
        for i, page in enumerate(mock_pages):
            page.extract_text.return_value = f"Page {i+1} text"

        mock_reader = MagicMock()
        mock_reader.pages = mock_pages
        mock_pdf_reader.return_value = mock_reader

        # Mock image conversion
        mock_image = MagicMock()
        mock_convert.return_value = [mock_image]

        # Create test PDF file
        test_pdf = tmp_path / "test_integration.pdf"
        test_pdf.write_bytes(b"fake pdf content")

        # Layer 1: Process document
        processor = DocumentProcessor(integration_db, "fake_api_key")

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"pdf"
            doc_id = processor.process_document(test_pdf)

        # Verify document was processed
        assert doc_id is not None
        doc = integration_db.get_document(doc_id)
        assert doc is not None

        # Layer 2: Access via MCP tools
        with patch('legal_doc_mcp_server.db', integration_db):
            import legal_doc_mcp_server as mcp

            # Test list_documents
            import asyncio
            list_result = asyncio.run(mcp.list_documents())

            assert "test_integration.pdf" in list_result

            # Test get_documents
            doc_result = asyncio.run(mcp.get_documents([doc_id]))

            assert "PAGE SUMMARIES" in doc_result
            assert "Page 1:" in doc_result

            # Test get_page_text
            page_result = asyncio.run(mcp.get_page_text(doc_id, [1]))

            assert "Page 1 text" in page_result


# ============================================================================
# Layer 2 → Layer 3 Integration
# ============================================================================

class TestLayer2ToLayer3Integration:
    """Test MCP server → Agent system integration."""

    @pytest.mark.asyncio
    async def test_agent_uses_mcp_tools(self, integration_db):
        """Test: Agent accesses documents via MCP tools."""

        # Add test document to database
        doc_id = integration_db.add_document(
            filename="agent_test.pdf",
            filepath="/data/agent_test.pdf",
            file_hash="hash"
        )

        for i in range(1, 4):
            integration_db.add_page(
                doc_id, i, f"Page {i} content", b"img", f"Page {i} summary"
            )

        integration_db.update_document_summary(
            doc_id, "Test document for agent", [2]
        )

        cursor = integration_db.conn.cursor()
        cursor.execute("UPDATE documents SET total_pages = ? WHERE doc_id = ?", (3, doc_id))
        integration_db.conn.commit()

        # Mock MCP server with this database
        with patch('legal_doc_mcp_server.db', integration_db):
            import legal_doc_mcp_server as mcp

            # Simulate agent using MCP tools
            docs_list = await mcp.list_documents()
            assert "agent_test.pdf" in docs_list

            doc_content = await mcp.get_documents([doc_id])
            assert "Page 1:" in doc_content
            assert "Page 2:" in doc_content

            page_text = await mcp.get_page_text(doc_id, [1])
            assert "Page 1 content" in page_text


# ============================================================================
# Layer 3 → Layer 4 Integration
# ============================================================================

class TestLayer3ToLayer4Integration:
    """Test Agent system → Web interface integration."""

    @patch('web_server.create_legal_risk_agent')
    def test_web_interface_invokes_agent(self, mock_create_agent, integration_db):
        """Test: Web interface → Agent execution."""

        from fastapi.testclient import TestClient

        # Mock agent
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [{"content": "Analysis complete"}]
        }
        mock_create_agent.return_value = mock_agent

        # Mock database
        with patch('web_server.LegalDocumentDatabase', return_value=integration_db):
            from web_server import app

            client = TestClient(app)

            # Create session
            session_response = client.post("/api/sessions")
            session_id = session_response.json()["session_id"]

            # Start analysis via WebSocket
            with client.websocket_connect(f"/ws/{session_id}") as websocket:
                websocket.receive_json()  # connection message

                # Send analysis request
                websocket.send_json({
                    "type": "start_analysis",
                    "message": "Analyze documents"
                })

                # Should invoke agent
                websocket.receive_json()  # analysis_started

                # Verify agent was invoked
                assert mock_agent.invoke.called


# ============================================================================
# Full Pipeline Integration Tests
# ============================================================================

class TestFullPipeline:
    """Test complete pipeline: PDF → Database → MCP → Agent → Web."""

    @patch('document_processor.convert_from_path')
    @patch('document_processor.pypdf.PdfReader')
    @patch('document_processor.anthropic.Anthropic')
    @patch('web_server.create_legal_risk_agent')
    def test_complete_workflow(
        self, mock_create_agent, mock_anthropic_doc,
        mock_pdf_reader, mock_convert, tmp_path
    ):
        """Test complete workflow from PDF ingestion to web interface analysis."""

        # Setup database
        db_path = tmp_path / "full_pipeline.db"
        db = LegalDocumentDatabase(str(db_path))

        try:
            # Step 1: Document Processing (Layer 1)
            mock_client = MagicMock()
            mock_anthropic_doc.return_value = mock_client

            page_response = MagicMock()
            page_response.content = [MagicMock(text="Page summary")]

            doc_response = MagicMock()
            doc_response.content = [MagicMock(text="""SUMMARY: Full pipeline test
SIGNIFICANT_PAGES: 1""")]

            mock_client.messages.create.side_effect = [page_response, doc_response]

            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test page content"
            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader

            mock_image = MagicMock()
            mock_convert.return_value = [mock_image]

            test_pdf = tmp_path / "pipeline_test.pdf"
            test_pdf.write_bytes(b"fake pdf")

            processor = DocumentProcessor(db, "fake_key")

            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b"pdf"
                doc_id = processor.process_document(test_pdf)

            # Verify document in database
            doc = db.get_document(doc_id)
            assert doc is not None

            # Step 2: MCP Server Access (Layer 2)
            with patch('legal_doc_mcp_server.db', db):
                import legal_doc_mcp_server as mcp
                import asyncio

                list_result = asyncio.run(mcp.list_documents())
                assert "pipeline_test.pdf" in list_result

            # Step 3: Agent Invocation (Layer 3)
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = {
                "messages": [{"content": "Pipeline test complete"}]
            }
            mock_create_agent.return_value = mock_agent

            # Step 4: Web Interface (Layer 4)
            from fastapi.testclient import TestClient

            with patch('web_server.LegalDocumentDatabase', return_value=db):
                from web_server import app

                client = TestClient(app)

                # Verify documents accessible via API
                docs_response = client.get("/api/documents")
                assert docs_response.status_code == 200

                docs_data = docs_response.json()
                assert len(docs_data["documents"]) == 1

                # Create session and start analysis
                session_response = client.post("/api/sessions")
                session_id = session_response.json()["session_id"]

                with client.websocket_connect(f"/ws/{session_id}") as websocket:
                    websocket.receive_json()  # connection

                    websocket.send_json({
                        "type": "start_analysis",
                        "message": "Full pipeline test"
                    })

                    # Receive updates
                    msg = websocket.receive_json()
                    assert msg["type"] == "analysis_started"

                    # Verify agent was invoked
                    assert mock_agent.invoke.called

        finally:
            db.close()


# ============================================================================
# Performance Integration Tests
# ============================================================================

class TestIntegrationPerformance:
    """Test performance across integrated layers."""

    @patch('document_processor.convert_from_path')
    @patch('document_processor.pypdf.PdfReader')
    @patch('document_processor.anthropic.Anthropic')
    def test_multiple_documents_pipeline(
        self, mock_anthropic, mock_pdf_reader, mock_convert, tmp_path
    ):
        """Test processing multiple documents through pipeline."""

        db_path = tmp_path / "multi_doc.db"
        db = LegalDocumentDatabase(str(db_path))

        try:
            # Setup mocks
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            page_response = MagicMock()
            page_response.content = [MagicMock(text="Page summary")]

            doc_response = MagicMock()
            doc_response.content = [MagicMock(text="""SUMMARY: Document summary
SIGNIFICANT_PAGES: 1""")]

            # Multiple responses for multiple documents
            mock_client.messages.create.side_effect = [
                page_response, doc_response,
                page_response, doc_response,
                page_response, doc_response
            ]

            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test content"
            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader

            mock_image = MagicMock()
            mock_convert.return_value = [mock_image]

            processor = DocumentProcessor(db, "fake_key")

            # Process multiple documents
            doc_ids = []
            for i in range(3):
                test_pdf = tmp_path / f"doc_{i}.pdf"
                test_pdf.write_bytes(b"fake pdf")

                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = b"pdf"
                    doc_id = processor.process_document(test_pdf)
                    doc_ids.append(doc_id)

            # Verify all documents in database
            all_docs = db.get_all_documents()
            assert len(all_docs) == 3

            # Test MCP access to all documents
            with patch('legal_doc_mcp_server.db', db):
                import legal_doc_mcp_server as mcp
                import asyncio

                list_result = asyncio.run(mcp.list_documents())

                for i in range(3):
                    assert f"doc_{i}.pdf" in list_result

        finally:
            db.close()


# ============================================================================
# Error Recovery Integration Tests
# ============================================================================

class TestIntegrationErrorRecovery:
    """Test error handling across integrated layers."""

    def test_database_error_propagation(self, integration_db):
        """Test how database errors propagate through layers."""

        # Force database error
        integration_db.conn.close()

        # Should handle gracefully in MCP layer
        with patch('legal_doc_mcp_server.db', integration_db):
            import legal_doc_mcp_server as mcp
            import asyncio

            result = asyncio.run(mcp.list_documents())

            assert "Error" in result

    @patch('web_server.create_legal_risk_agent')
    def test_agent_error_to_web_interface(self, mock_create_agent):
        """Test agent errors propagate to web interface."""

        from fastapi.testclient import TestClient

        # Mock agent to raise error
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = Exception("Agent error")
        mock_create_agent.return_value = mock_agent

        with patch('web_server.LegalDocumentDatabase'):
            from web_server import app

            client = TestClient(app)

            session_response = client.post("/api/sessions")
            session_id = session_response.json()["session_id"]

            with client.websocket_connect(f"/ws/{session_id}") as websocket:
                websocket.receive_json()  # connection

                websocket.send_json({
                    "type": "start_analysis",
                    "message": "Test"
                })

                websocket.receive_json()  # analysis_started

                # Should receive error message
                msg = websocket.receive_json()
                assert msg["type"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
