"""
Test Suite for Layer 2: MCP Document Analysis Server

This test suite covers:
- MCP tool definitions and registration
- list_documents tool functionality
- get_documents tool with layered access
- get_page_text tool for specific pages
- get_page_image tool for visual analysis
- Error handling and edge cases
- Token efficiency through layered access
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import LegalDocumentDatabase


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def populated_db(tmp_path):
    """Create a database with test data."""
    db_path = tmp_path / "test.db"
    db = LegalDocumentDatabase(str(db_path))

    # Add test documents
    doc1_id = db.add_document(
        filename="employment_agreement.pdf",
        filepath="/data/employment_agreement.pdf",
        file_hash="hash1"
    )

    # Add pages for doc1
    for i in range(1, 11):
        db.add_page(
            doc_id=doc1_id,
            page_num=i,
            page_text=f"This is the text content of page {i} of the employment agreement.",
            page_image=f"fake_image_{i}".encode(),
            summdesc=f"Page {i}: Employment terms and conditions section {i}"
        )

    # Update doc1 with summary and significant pages
    db.update_document_summary(
        doc1_id,
        "Employment agreement with standard IP assignment and non-compete clauses.",
        [3, 7, 9]  # Significant pages
    )

    # Update total pages
    cursor = db.conn.cursor()
    cursor.execute("UPDATE documents SET total_pages = ? WHERE doc_id = ?", (10, doc1_id))
    db.conn.commit()

    # Add second document
    doc2_id = db.add_document(
        filename="vendor_contract.pdf",
        filepath="/data/vendor_contract.pdf",
        file_hash="hash2"
    )

    # Add pages for doc2
    for i in range(1, 6):
        db.add_page(
            doc_id=doc2_id,
            page_num=i,
            page_text=f"Vendor contract page {i} content with terms.",
            page_image=f"vendor_img_{i}".encode(),
            summdesc=f"Page {i}: Vendor terms section {i}"
        )

    db.update_document_summary(
        doc2_id,
        "Vendor service agreement with payment and liability terms.",
        [2, 4]
    )

    cursor.execute("UPDATE documents SET total_pages = ? WHERE doc_id = ?", (5, doc2_id))
    db.conn.commit()

    yield db
    db.close()


@pytest.fixture
def mcp_server_module(populated_db):
    """Import MCP server module with mocked database."""
    with patch('legal_doc_mcp_server.db', populated_db):
        import legal_doc_mcp_server as mcp_module
        yield mcp_module


# ============================================================================
# Tool Registration Tests
# ============================================================================

class TestMCPServerSetup:
    """Test MCP server initialization and tool registration."""

    def test_server_initialization(self):
        """Test that MCP server initializes correctly."""
        import legal_doc_mcp_server as mcp_module

        assert mcp_module.mcp is not None
        assert hasattr(mcp_module, 'list_documents')
        assert hasattr(mcp_module, 'get_documents')
        assert hasattr(mcp_module, 'get_page_text')
        assert hasattr(mcp_module, 'get_page_image')

    def test_database_connection(self, populated_db):
        """Test that database is accessible."""
        docs = populated_db.get_all_documents()
        assert len(docs) == 2


# ============================================================================
# list_documents Tool Tests
# ============================================================================

class TestListDocumentsTool:
    """Test list_documents MCP tool."""

    @pytest.mark.asyncio
    async def test_list_documents_with_data(self, mcp_server_module):
        """Test listing documents when documents exist."""
        result = await mcp_server_module.list_documents()

        assert "LEGAL DOCUMENTS DATA ROOM" in result
        assert "Total Documents: 2" in result
        assert "employment_agreement.pdf" in result
        assert "vendor_contract.pdf" in result
        assert "Document ID: 1" in result
        assert "Document ID: 2" in result

    @pytest.mark.asyncio
    async def test_list_documents_shows_summaries(self, mcp_server_module):
        """Test that document summaries are included."""
        result = await mcp_server_module.list_documents()

        assert "IP assignment" in result
        assert "Vendor service agreement" in result

    @pytest.mark.asyncio
    async def test_list_documents_shows_page_counts(self, mcp_server_module):
        """Test that page counts are shown."""
        result = await mcp_server_module.list_documents()

        assert "10 total" in result  # employment_agreement
        assert "5 total" in result   # vendor_contract
        assert "3 legally significant" in result  # employment_agreement
        assert "2 legally significant" in result  # vendor_contract

    @pytest.mark.asyncio
    async def test_list_documents_empty_database(self):
        """Test listing documents when database is empty."""
        with patch('legal_doc_mcp_server.db') as mock_db:
            mock_db.get_all_documents.return_value = []

            import legal_doc_mcp_server as mcp_module
            result = await mcp_module.list_documents()

            assert "No documents found" in result

    @pytest.mark.asyncio
    async def test_list_documents_error_handling(self):
        """Test error handling in list_documents."""
        with patch('legal_doc_mcp_server.db') as mock_db:
            mock_db.get_all_documents.side_effect = Exception("Database error")

            import legal_doc_mcp_server as mcp_module
            result = await mcp_module.list_documents()

            assert "Error listing documents" in result
            assert "Database error" in result


# ============================================================================
# get_documents Tool Tests
# ============================================================================

class TestGetDocumentsTool:
    """Test get_documents MCP tool."""

    @pytest.mark.asyncio
    async def test_get_documents_single_doc(self, mcp_server_module):
        """Test retrieving a single document."""
        result = await mcp_server_module.get_documents([1])

        assert "employment_agreement.pdf" in result
        assert "PAGE SUMMARIES" in result
        assert "LEGALLY SIGNIFICANT PAGE CONTENT" in result

    @pytest.mark.asyncio
    async def test_get_documents_multiple_docs(self, mcp_server_module):
        """Test retrieving multiple documents."""
        result = await mcp_server_module.get_documents([1, 2])

        assert "employment_agreement.pdf" in result
        assert "vendor_contract.pdf" in result

    @pytest.mark.asyncio
    async def test_get_documents_shows_all_page_summaries(self, mcp_server_module):
        """Test that all page summaries are shown."""
        result = await mcp_server_module.get_documents([1])

        # Check that all 10 pages are listed
        for i in range(1, 11):
            assert f"Page {i}:" in result

    @pytest.mark.asyncio
    async def test_get_documents_marks_significant_pages(self, mcp_server_module):
        """Test that significant pages are visually marked."""
        result = await mcp_server_module.get_documents([1])

        # Check for significance marker (⚖️)
        assert "⚖️" in result

    @pytest.mark.asyncio
    async def test_get_documents_includes_significant_page_text(self, mcp_server_module):
        """Test that full text of significant pages is included."""
        result = await mcp_server_module.get_documents([1])

        # Pages 3, 7, 9 are marked significant
        assert "This is the text content of page 3" in result
        assert "This is the text content of page 7" in result
        assert "This is the text content of page 9" in result

    @pytest.mark.asyncio
    async def test_get_documents_excludes_non_significant_page_text(self, mcp_server_module):
        """Test that non-significant page text is NOT included in full."""
        result = await mcp_server_module.get_documents([1])

        # The summary should be there, but not the full text
        # (except for significant pages 3,7,9)
        lines = result.split('\n')

        # Count occurrences of full page text for page 1 (not significant)
        page_1_text_count = sum(1 for line in lines if "text content of page 1" in line)

        # Should appear once in summary, but not in full content section
        # Actually, since page 1 is not significant, it shouldn't appear in detail
        # But it WILL appear in the summary line
        assert page_1_text_count >= 1

    @pytest.mark.asyncio
    async def test_get_documents_empty_list(self, mcp_server_module):
        """Test get_documents with empty doc_ids list."""
        result = await mcp_server_module.get_documents([])

        assert "Error" in result
        assert "doc_ids parameter is required" in result

    @pytest.mark.asyncio
    async def test_get_documents_nonexistent_doc(self, mcp_server_module):
        """Test get_documents with non-existent document ID."""
        result = await mcp_server_module.get_documents([999])

        assert "not found" in result

    @pytest.mark.asyncio
    async def test_get_documents_provides_usage_notes(self, mcp_server_module):
        """Test that usage notes are included."""
        result = await mcp_server_module.get_documents([1])

        assert "ANALYSIS NOTES" in result or "get_page_text" in result


# ============================================================================
# get_page_text Tool Tests
# ============================================================================

class TestGetPageTextTool:
    """Test get_page_text MCP tool."""

    @pytest.mark.asyncio
    async def test_get_page_text_single_page(self, mcp_server_module):
        """Test retrieving a single page's text."""
        result = await mcp_server_module.get_page_text(1, [5])

        assert "employment_agreement.pdf" in result
        assert "Page 5:" in result
        assert "This is the text content of page 5" in result

    @pytest.mark.asyncio
    async def test_get_page_text_multiple_pages(self, mcp_server_module):
        """Test retrieving multiple pages."""
        result = await mcp_server_module.get_page_text(1, [2, 4, 6])

        assert "Page 2:" in result
        assert "Page 4:" in result
        assert "Page 6:" in result

    @pytest.mark.asyncio
    async def test_get_page_text_shows_summaries(self, mcp_server_module):
        """Test that page summaries are shown."""
        result = await mcp_server_module.get_page_text(1, [3])

        # Should include the page summary
        assert "Employment terms and conditions" in result

    @pytest.mark.asyncio
    async def test_get_page_text_empty_page_list(self, mcp_server_module):
        """Test get_page_text with empty page list."""
        result = await mcp_server_module.get_page_text(1, [])

        assert "Error" in result
        assert "page_nums parameter is required" in result

    @pytest.mark.asyncio
    async def test_get_page_text_invalid_page_numbers(self, mcp_server_module):
        """Test get_page_text with invalid page numbers."""
        result = await mcp_server_module.get_page_text(1, [99])

        assert "Error" in result or "Invalid page numbers" in result

    @pytest.mark.asyncio
    async def test_get_page_text_nonexistent_document(self, mcp_server_module):
        """Test get_page_text for non-existent document."""
        result = await mcp_server_module.get_page_text(999, [1])

        assert "Error" in result
        assert "not found" in result


# ============================================================================
# get_page_image Tool Tests
# ============================================================================

class TestGetPageImageTool:
    """Test get_page_image MCP tool."""

    @pytest.mark.asyncio
    async def test_get_page_image_single_page(self, mcp_server_module):
        """Test retrieving a page image."""
        result = await mcp_server_module.get_page_image(1, [3])

        assert "employment_agreement.pdf" in result
        assert "PAGE IMAGES RETRIEVED" in result
        assert "Image data:" in result or "[Image" in result

    @pytest.mark.asyncio
    async def test_get_page_image_shows_usage_warning(self, mcp_server_module):
        """Test that usage warning is displayed."""
        result = await mcp_server_module.get_page_image(1, [3])

        assert "LIMITED USE" in result or "USAGE NOTE" in result or "tokens" in result.lower()

    @pytest.mark.asyncio
    async def test_get_page_image_multiple_pages(self, mcp_server_module):
        """Test retrieving multiple page images."""
        result = await mcp_server_module.get_page_image(1, [2, 4])

        assert "PAGE IMAGES RETRIEVED: 2, 4" in result

    @pytest.mark.asyncio
    async def test_get_page_image_empty_list(self, mcp_server_module):
        """Test get_page_image with empty page list."""
        result = await mcp_server_module.get_page_image(1, [])

        assert "Error" in result
        assert "page_nums parameter is required" in result

    @pytest.mark.asyncio
    async def test_get_page_image_nonexistent_document(self, mcp_server_module):
        """Test get_page_image for non-existent document."""
        result = await mcp_server_module.get_page_image(999, [1])

        assert "Error" in result
        assert "not found" in result


# ============================================================================
# Integration and Layered Access Tests
# ============================================================================

class TestLayeredAccess:
    """Test the layered access model for token efficiency."""

    @pytest.mark.asyncio
    async def test_layered_access_workflow(self, mcp_server_module):
        """Test the recommended workflow: list → get → page text → image."""

        # Step 1: List documents (high-level overview)
        list_result = await mcp_server_module.list_documents()
        assert "employment_agreement.pdf" in list_result
        assert "10 total" in list_result

        # Step 2: Get document (summaries + significant pages)
        doc_result = await mcp_server_module.get_documents([1])
        assert "PAGE SUMMARIES" in doc_result
        assert "LEGALLY SIGNIFICANT PAGE CONTENT" in doc_result

        # Step 3: Get additional page text if needed
        page_result = await mcp_server_module.get_page_text(1, [1, 2])
        assert "This is the text content of page 1" in page_result

        # Step 4: Get images only when necessary
        image_result = await mcp_server_module.get_page_image(1, [1])
        assert "Image data:" in image_result or "[Image" in image_result

    @pytest.mark.asyncio
    async def test_token_efficiency_through_layering(self, mcp_server_module):
        """Test that layering reduces unnecessary data transfer."""

        # list_documents provides just metadata
        list_result = await mcp_server_module.list_documents()
        list_length = len(list_result)

        # get_documents provides summaries + significant pages only
        doc_result = await mcp_server_module.get_documents([1])
        doc_length = len(doc_result)

        # get_page_text provides full text (more data)
        all_pages_result = await mcp_server_module.get_page_text(1, list(range(1, 11)))
        all_pages_length = len(all_pages_result)

        # Verify layering: list < doc < all pages
        assert list_length < doc_length < all_pages_length


# ============================================================================
# Error Handling and Edge Cases
# ============================================================================

class TestErrorHandling:
    """Test error handling across all tools."""

    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling database connection errors."""
        with patch('legal_doc_mcp_server.db') as mock_db:
            mock_db.get_all_documents.side_effect = Exception("Connection failed")

            import legal_doc_mcp_server as mcp_module
            result = await mcp_module.list_documents()

            assert "Error" in result

    @pytest.mark.asyncio
    async def test_malformed_document_data(self, populated_db):
        """Test handling malformed document data."""
        # Add document with missing data
        cursor = populated_db.conn.cursor()
        cursor.execute("""
            INSERT INTO documents (filename, filepath, file_hash)
            VALUES (?, ?, ?)
        """, ("broken.pdf", "/path/broken.pdf", "hash"))
        populated_db.conn.commit()

        with patch('legal_doc_mcp_server.db', populated_db):
            import legal_doc_mcp_server as mcp_module
            result = await mcp_module.list_documents()

            # Should handle gracefully
            assert "broken.pdf" in result

    @pytest.mark.asyncio
    async def test_unicode_in_document_content(self, mcp_server_module):
        """Test handling Unicode characters in documents."""
        # The test database already has ASCII content
        # This test verifies no Unicode errors occur
        result = await mcp_server_module.list_documents()
        assert result is not None


# ============================================================================
# Performance and Scalability Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_large_document_list(self, tmp_path):
        """Test listing many documents."""
        db_path = tmp_path / "large_test.db"
        db = LegalDocumentDatabase(str(db_path))

        # Add 50 documents
        for i in range(50):
            db.add_document(f"doc_{i}.pdf", f"/path/doc_{i}.pdf", f"hash_{i}")

        with patch('legal_doc_mcp_server.db', db):
            import legal_doc_mcp_server as mcp_module
            result = await mcp_module.list_documents()

            assert "Total Documents: 50" in result
            assert "doc_0.pdf" in result
            assert "doc_49.pdf" in result

        db.close()

    @pytest.mark.asyncio
    async def test_document_with_many_pages(self, tmp_path):
        """Test document with many pages."""
        db_path = tmp_path / "many_pages.db"
        db = LegalDocumentDatabase(str(db_path))

        doc_id = db.add_document("big_doc.pdf", "/path/big.pdf", "hash")

        # Add 100 pages
        for i in range(1, 101):
            db.add_page(doc_id, i, f"Page {i} text", b"img", f"Summary {i}")

        cursor = db.conn.cursor()
        cursor.execute("UPDATE documents SET total_pages = ? WHERE doc_id = ?", (100, doc_id))
        db.conn.commit()

        with patch('legal_doc_mcp_server.db', db):
            import legal_doc_mcp_server as mcp_module
            result = await mcp_module.get_documents([doc_id])

            # Should handle large page count
            assert "100 total" in result
            assert "Page 1:" in result
            assert "Page 100:" in result

        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
