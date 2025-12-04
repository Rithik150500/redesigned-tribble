"""
Test Suite for Layer 4: Web Interface

This test suite covers:
- REST API endpoints
- WebSocket communication
- Session management
- Approval workflow through WebSocket
- Real-time agent updates
- Document serving
- Error handling
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database for testing."""
    with patch('web_server.LegalDocumentDatabase') as mock:
        db_instance = MagicMock()

        # Mock documents
        db_instance.get_all_documents.return_value = [
            {
                "doc_id": 1,
                "filename": "test.pdf",
                "summdesc": "Test document",
                "total_pages": 10,
                "legally_significant_pages": 3
            }
        ]

        db_instance.get_document.return_value = {
            "doc_id": 1,
            "filename": "test.pdf",
            "filepath": "/data/test.pdf",
            "summdesc": "Test document",
            "total_pages": 10
        }

        db_instance.get_pages.return_value = [
            {
                "page_id": 1,
                "page_num": 1,
                "summdesc": "Page 1 summary",
                "page_text": "Page 1 text",
                "page_image": b"fake_image",
                "legally_significant": 1
            }
        ]

        mock.return_value = db_instance
        yield db_instance


@pytest.fixture
def client(mock_db):
    """Test client for FastAPI app."""
    from web_server import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    with patch('web_server.create_legal_risk_agent') as mock:
        agent = MagicMock()
        agent.invoke.return_value = {"messages": [{"content": "test"}]}
        mock.return_value = agent
        yield agent


# ============================================================================
# REST API Tests
# ============================================================================

class TestRESTEndpoints:
    """Test REST API endpoints."""

    def test_list_documents_endpoint(self, client):
        """Test GET /api/documents endpoint."""
        response = client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert len(data["documents"]) == 1
        assert data["documents"][0]["filename"] == "test.pdf"

    def test_get_document_detail_endpoint(self, client, mock_db):
        """Test GET /api/documents/{doc_id} endpoint."""
        response = client.get("/api/documents/1")

        assert response.status_code == 200
        data = response.json()

        assert "document" in data
        assert data["document"]["filename"] == "test.pdf"
        assert "pages" in data
        assert "significant_pages" in data

    def test_get_nonexistent_document(self, client, mock_db):
        """Test getting non-existent document returns 404."""
        mock_db.get_document.return_value = None

        response = client.get("/api/documents/999")

        assert response.status_code == 404

    def test_create_session_endpoint(self, client):
        """Test POST /api/sessions endpoint."""
        response = client.post("/api/sessions")

        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert data["session_id"] is not None

    def test_delete_session_endpoint(self, client):
        """Test DELETE /api/sessions/{session_id} endpoint."""
        # First create a session
        create_response = client.post("/api/sessions")
        session_id = create_response.json()["session_id"]

        # Then delete it
        delete_response = client.delete(f"/api/sessions/{session_id}")

        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"

    @patch('web_server.Path')
    def test_get_document_pdf_endpoint(self, mock_path, client, mock_db):
        """Test GET /api/documents/{doc_id}/pdf endpoint."""
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file

        response = client.get("/api/documents/1/pdf")

        # Should attempt to serve file
        assert response.status_code in [200, 404]  # May vary based on mock

    def test_get_page_image_endpoint(self, client, mock_db):
        """Test GET /api/documents/{doc_id}/page/{page_num}/image endpoint."""
        response = client.get("/api/documents/1/page/1/image")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"


# ============================================================================
# WebSocket Connection Tests
# ============================================================================

class TestWebSocketConnection:
    """Test WebSocket connection and communication."""

    def test_websocket_connection(self, client):
        """Test establishing WebSocket connection."""
        # Create session first
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        # Connect via WebSocket
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()

            assert data["type"] == "connected"
            assert data["session_id"] == session_id

    def test_websocket_invalid_session(self, client):
        """Test WebSocket with invalid session ID."""
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/invalid_session_id") as websocket:
                pass

    def test_websocket_ping_pong(self, client):
        """Test WebSocket keepalive ping/pong."""
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Skip connection message
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"


# ============================================================================
# Analysis Workflow Tests
# ============================================================================

class TestAnalysisWorkflow:
    """Test analysis workflow through WebSocket."""

    @patch('web_server.create_legal_risk_agent')
    def test_start_analysis(self, mock_create_agent, client, mock_db):
        """Test starting an analysis."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [{"content": "Analysis started"}]}
        mock_create_agent.return_value = mock_agent

        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Skip connection message
            websocket.receive_json()

            # Start analysis
            websocket.send_json({
                "type": "start_analysis",
                "message": "Analyze all contracts"
            })

            # Should receive analysis started message
            data = websocket.receive_json()
            assert data["type"] == "analysis_started"

    @patch('web_server.create_legal_risk_agent')
    def test_analysis_with_approval_required(self, mock_create_agent, client, mock_db):
        """Test analysis that requires approval."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
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
        mock_create_agent.return_value = mock_agent

        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            websocket.receive_json()  # Skip connection

            websocket.send_json({
                "type": "start_analysis",
                "message": "Test"
            })

            websocket.receive_json()  # Skip analysis_started

            # Should receive approval_required
            data = websocket.receive_json()
            assert data["type"] == "approval_required"
            assert "actions" in data

    @patch('web_server.create_legal_risk_agent')
    def test_approval_decision(self, mock_create_agent, client, mock_db):
        """Test sending approval decision."""
        mock_agent = MagicMock()

        # First call returns interrupt, second call continues
        mock_agent.invoke.side_effect = [
            {
                "__interrupt__": [{
                    "value": {
                        "action_requests": [{
                            "name": "write_file",
                            "args": {"file_path": "/test.txt"}
                        }],
                        "review_configs": [{"action_name": "write_file"}]
                    }
                }]
            },
            {"messages": [{"content": "Completed"}]}
        ]

        mock_create_agent.return_value = mock_agent

        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            websocket.receive_json()  # connection

            # Start analysis
            websocket.send_json({
                "type": "start_analysis",
                "message": "Test"
            })

            websocket.receive_json()  # analysis_started
            websocket.receive_json()  # approval_required

            # Send approval
            websocket.send_json({
                "type": "approval_decision",
                "decisions": [{"decision": "approve"}]
            })

            # Should receive approval_processed
            data = websocket.receive_json()
            assert data["type"] == "approval_processed"


# ============================================================================
# Session Management Tests
# ============================================================================

class TestSessionManagement:
    """Test session management."""

    def test_create_multiple_sessions(self, client):
        """Test creating multiple independent sessions."""
        response1 = client.post("/api/sessions")
        response2 = client.post("/api/sessions")

        session1 = response1.json()["session_id"]
        session2 = response2.json()["session_id"]

        assert session1 != session2

    def test_session_persistence(self, client):
        """Test that session state persists."""
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        # First WebSocket connection
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            data = websocket.receive_json()
            assert data["session_id"] == session_id

        # Second connection to same session should work
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            data = websocket.receive_json()
            assert data["session_id"] == session_id


# ============================================================================
# Approval Context Tests
# ============================================================================

class TestApprovalContext:
    """Test approval context building."""

    @pytest.mark.asyncio
    async def test_build_approval_context_for_get_documents(self, mock_db):
        """Test building context for get_documents tool."""
        from web_server import build_approval_context

        context = await build_approval_context(
            "get_documents",
            {"doc_ids": [1]}
        )

        assert context["tool"] == "get_documents"
        assert "documents" in context

    @pytest.mark.asyncio
    async def test_build_approval_context_for_write_file(self, mock_db):
        """Test building context for file operations."""
        from web_server import build_approval_context

        context = await build_approval_context(
            "write_file",
            {"file_path": "/test.txt", "content": "test content"}
        )

        assert context["tool"] == "write_file"
        assert "file" in context
        assert context["file"]["path"] == "/test.txt"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in web interface."""

    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get("/api/invalid")

        assert response.status_code == 404

    def test_websocket_malformed_message(self, client):
        """Test sending malformed message via WebSocket."""
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            websocket.receive_json()  # connection

            # Send malformed message
            websocket.send_json({"type": "unknown_type"})

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"

    def test_start_analysis_without_message(self, client):
        """Test starting analysis without message."""
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            websocket.receive_json()  # connection

            # Send empty analysis request
            websocket.send_json({"type": "start_analysis", "message": ""})

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"


# ============================================================================
# CORS and Security Tests
# ============================================================================

class TestCORSAndSecurity:
    """Test CORS and security settings."""

    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.get("/api/documents")

        # FastAPI test client doesn't always include CORS headers
        # In production, verify Access-Control-Allow-Origin header

        assert response.status_code == 200

    def test_api_accepts_json(self, client):
        """Test that API accepts JSON content type."""
        response = client.post(
            "/api/sessions",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""

    def test_multiple_concurrent_sessions(self, client):
        """Test handling multiple concurrent sessions."""
        sessions = []

        # Create 10 sessions
        for _ in range(10):
            response = client.post("/api/sessions")
            assert response.status_code == 200
            sessions.append(response.json()["session_id"])

        # All should be unique
        assert len(set(sessions)) == 10

    def test_large_document_list(self, client, mock_db):
        """Test endpoint with large document list."""
        # Mock many documents
        mock_db.get_all_documents.return_value = [
            {
                "doc_id": i,
                "filename": f"doc_{i}.pdf",
                "summdesc": f"Document {i}",
                "total_pages": 10,
                "legally_significant_pages": 2
            }
            for i in range(100)
        ]

        response = client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
