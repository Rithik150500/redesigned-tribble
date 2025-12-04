"""
Test Suite for Layer 1: Document Processing & Database

This test suite covers:
- Database schema creation and integrity
- Document ingestion and storage
- Page extraction and processing
- AI summarization (mocked for testing)
- Legally significant page detection
- Error handling and edge cases
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import io

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import LegalDocumentDatabase
from document_processor import DocumentProcessor


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = f.name

    db = LegalDocumentDatabase(db_path)
    yield db

    db.close()
    os.unlink(db_path)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing without API calls."""
    with patch('document_processor.anthropic.Anthropic') as mock:
        client = MagicMock()
        mock.return_value = client

        # Mock page summarization response
        page_response = MagicMock()
        page_response.content = [MagicMock(text="Mock page summary about confidentiality provisions.")]

        # Mock document analysis response
        doc_response = MagicMock()
        doc_response.content = [MagicMock(text="""SUMMARY: This is a test employment agreement with standard clauses.
SIGNIFICANT_PAGES: 2,4,6""")]

        # Set up the mock to return different responses
        client.messages.create.side_effect = [page_response, page_response, page_response,
                                              page_response, page_response, doc_response]

        yield client


@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF for testing (we'll mock the actual PDF operations)."""
    return Path("/tmp/test_document.pdf")


# ============================================================================
# Database Tests
# ============================================================================

class TestDatabaseSchema:
    """Test database schema creation and integrity."""

    def test_database_initialization(self, temp_db):
        """Test that database tables are created correctly."""
        cursor = temp_db.conn.cursor()

        # Check documents table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='documents'
        """)
        assert cursor.fetchone() is not None

        # Check pages table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='pages'
        """)
        assert cursor.fetchone() is not None

    def test_documents_table_schema(self, temp_db):
        """Test documents table has correct columns."""
        cursor = temp_db.conn.cursor()
        cursor.execute("PRAGMA table_info(documents)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {
            'doc_id', 'filename', 'filepath', 'summdesc',
            'total_pages', 'legally_significant_pages',
            'processed_at', 'file_hash'
        }
        assert expected_columns.issubset(columns)

    def test_pages_table_schema(self, temp_db):
        """Test pages table has correct columns."""
        cursor = temp_db.conn.cursor()
        cursor.execute("PRAGMA table_info(pages)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {
            'page_id', 'doc_id', 'page_num', 'summdesc',
            'page_text', 'page_image', 'legally_significant'
        }
        assert expected_columns.issubset(columns)

    def test_indexes_created(self, temp_db):
        """Test that indexes are created for performance."""
        cursor = temp_db.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND sql IS NOT NULL
        """)
        indexes = {row[0] for row in cursor.fetchall()}

        assert 'idx_pages_doc_id' in indexes
        assert 'idx_pages_legally_significant' in indexes


class TestDocumentOperations:
    """Test document CRUD operations."""

    def test_add_document(self, temp_db):
        """Test adding a document to the database."""
        doc_id = temp_db.add_document(
            filename="test.pdf",
            filepath="/path/to/test.pdf",
            file_hash="abc123"
        )

        assert doc_id is not None
        assert doc_id > 0

        # Verify document was added
        doc = temp_db.get_document(doc_id)
        assert doc['filename'] == "test.pdf"
        assert doc['filepath'] == "/path/to/test.pdf"
        assert doc['file_hash'] == "abc123"

    def test_add_duplicate_filename(self, temp_db):
        """Test that duplicate filenames are rejected."""
        temp_db.add_document(
            filename="test.pdf",
            filepath="/path/to/test.pdf",
            file_hash="abc123"
        )

        # Try to add duplicate
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.add_document(
                filename="test.pdf",
                filepath="/different/path.pdf",
                file_hash="def456"
            )

    def test_get_nonexistent_document(self, temp_db):
        """Test getting a document that doesn't exist."""
        doc = temp_db.get_document(999)
        assert doc is None

    def test_get_all_documents_empty(self, temp_db):
        """Test getting all documents when database is empty."""
        docs = temp_db.get_all_documents()
        assert docs == []

    def test_get_all_documents(self, temp_db):
        """Test getting all documents."""
        # Add multiple documents
        temp_db.add_document("doc1.pdf", "/path/doc1.pdf", "hash1")
        temp_db.add_document("doc2.pdf", "/path/doc2.pdf", "hash2")
        temp_db.add_document("doc3.pdf", "/path/doc3.pdf", "hash3")

        docs = temp_db.get_all_documents()
        assert len(docs) == 3
        assert docs[0]['filename'] == "doc1.pdf"
        assert docs[1]['filename'] == "doc2.pdf"


class TestPageOperations:
    """Test page CRUD operations."""

    def test_add_page(self, temp_db):
        """Test adding a page to a document."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        page_id = temp_db.add_page(
            doc_id=doc_id,
            page_num=1,
            page_text="This is page text",
            page_image=b"fake_image_data",
            summdesc="Summary of page 1"
        )

        assert page_id is not None
        assert page_id > 0

    def test_get_pages(self, temp_db):
        """Test retrieving pages for a document."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        # Add multiple pages
        temp_db.add_page(doc_id, 1, "Page 1 text", b"img1", "Summary 1")
        temp_db.add_page(doc_id, 2, "Page 2 text", b"img2", "Summary 2")
        temp_db.add_page(doc_id, 3, "Page 3 text", b"img3", "Summary 3")

        pages = temp_db.get_pages(doc_id)
        assert len(pages) == 3
        assert pages[0]['page_num'] == 1
        assert pages[1]['page_num'] == 2
        assert pages[2]['page_num'] == 3

    def test_get_specific_pages(self, temp_db):
        """Test retrieving specific page numbers."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        # Add pages
        for i in range(1, 11):
            temp_db.add_page(doc_id, i, f"Page {i}", b"img", f"Summary {i}")

        # Get specific pages
        pages = temp_db.get_pages(doc_id, [2, 5, 8])
        assert len(pages) == 3
        assert pages[0]['page_num'] == 2
        assert pages[1]['page_num'] == 5
        assert pages[2]['page_num'] == 8

    def test_duplicate_page_rejected(self, temp_db):
        """Test that duplicate pages for same document are rejected."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        temp_db.add_page(doc_id, 1, "Page 1", b"img1", "Summary 1")

        with pytest.raises(sqlite3.IntegrityError):
            temp_db.add_page(doc_id, 1, "Duplicate", b"img2", "Duplicate")


class TestDocumentSummaryAndSignificance:
    """Test document summary updates and significance marking."""

    def test_update_document_summary(self, temp_db):
        """Test updating document with summary and significant pages."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        # Add pages
        for i in range(1, 6):
            temp_db.add_page(doc_id, i, f"Page {i}", b"img", f"Summary {i}")

        # Update with summary and significant pages
        summary = "This document contains employment terms."
        significant_pages = [2, 4]

        temp_db.update_document_summary(doc_id, summary, significant_pages)

        # Verify document updated
        doc = temp_db.get_document(doc_id)
        assert doc['summdesc'] == summary
        assert doc['legally_significant_pages'] == 2

        # Verify pages marked as significant
        pages = temp_db.get_pages(doc_id)
        assert pages[1]['legally_significant'] == 1  # Page 2
        assert pages[3]['legally_significant'] == 1  # Page 4
        assert pages[0]['legally_significant'] == 0  # Page 1

    def test_get_legally_significant_pages(self, temp_db):
        """Test retrieving only legally significant pages."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        # Add pages
        for i in range(1, 6):
            temp_db.add_page(doc_id, i, f"Page {i}", b"img", f"Summary {i}")

        # Mark pages 2 and 4 as significant
        temp_db.update_document_summary(doc_id, "Summary", [2, 4])

        # Get only significant pages
        sig_pages = temp_db.get_legally_significant_pages(doc_id)
        assert len(sig_pages) == 2
        assert sig_pages[0]['page_num'] == 2
        assert sig_pages[1]['page_num'] == 4


# ============================================================================
# Document Processor Tests
# ============================================================================

class TestDocumentProcessor:
    """Test document processor functionality."""

    def test_processor_initialization(self, temp_db, mock_anthropic_client):
        """Test processor initializes correctly."""
        processor = DocumentProcessor(temp_db, "fake_api_key")
        assert processor.db == temp_db
        assert processor.client is not None

    def test_calculate_file_hash(self, temp_db):
        """Test file hash calculation."""
        processor = DocumentProcessor(temp_db, "fake_api_key")

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)

        try:
            hash1 = processor._calculate_file_hash(temp_path)
            assert hash1 is not None
            assert len(hash1) == 64  # SHA256 produces 64 hex characters

            # Same file should produce same hash
            hash2 = processor._calculate_file_hash(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)

    @patch('document_processor.pypdf.PdfReader')
    def test_extract_text_from_page(self, mock_pdf_reader, temp_db):
        """Test text extraction from PDF page."""
        processor = DocumentProcessor(temp_db, "fake_api_key")

        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "  Sample text from PDF  "
        mock_pdf_reader.return_value.pages = [mock_page]

        reader = mock_pdf_reader.return_value
        text = processor._extract_text_from_page(reader, 0)

        assert text == "Sample text from PDF"

    @patch('document_processor.pypdf.PdfReader')
    def test_extract_text_handles_errors(self, mock_pdf_reader, temp_db):
        """Test text extraction handles errors gracefully."""
        processor = DocumentProcessor(temp_db, "fake_api_key")

        # Mock PDF reader to raise error
        mock_page = MagicMock()
        mock_page.extract_text.side_effect = Exception("PDF error")
        mock_pdf_reader.return_value.pages = [mock_page]

        reader = mock_pdf_reader.return_value
        text = processor._extract_text_from_page(reader, 0)

        assert text == ""

    @patch('document_processor.convert_from_path')
    def test_render_page_as_image(self, mock_convert, temp_db, sample_pdf_path):
        """Test rendering PDF page as image."""
        processor = DocumentProcessor(temp_db, "fake_api_key")

        # Mock PIL Image
        mock_image = MagicMock()
        mock_convert.return_value = [mock_image]

        image_bytes = processor._render_page_as_image(sample_pdf_path, 0)

        # Verify convert_from_path was called with correct parameters
        mock_convert.assert_called_once()
        assert mock_convert.call_args[1]['dpi'] == 150

        # Verify image was saved
        mock_image.save.assert_called_once()

    @patch('document_processor.convert_from_path')
    def test_render_page_handles_errors(self, mock_convert, temp_db, sample_pdf_path):
        """Test image rendering handles errors gracefully."""
        processor = DocumentProcessor(temp_db, "fake_api_key")

        mock_convert.side_effect = Exception("Rendering error")

        image_bytes = processor._render_page_as_image(sample_pdf_path, 0)
        assert image_bytes == b""


class TestDocumentProcessingIntegration:
    """Integration tests for full document processing pipeline."""

    @patch('document_processor.convert_from_path')
    @patch('document_processor.pypdf.PdfReader')
    @patch('builtins.open', create=True)
    def test_process_document_full_pipeline(self, mock_open, mock_pdf_reader,
                                           mock_convert, temp_db,
                                           mock_anthropic_client, sample_pdf_path):
        """Test complete document processing pipeline."""
        # Setup mocks
        mock_open.return_value.__enter__.return_value.read.return_value = b"pdf content"

        # Mock PDF pages
        mock_pages = []
        for i in range(5):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = f"Text from page {i+1}"
            mock_pages.append(mock_page)

        mock_reader = MagicMock()
        mock_reader.pages = mock_pages
        mock_pdf_reader.return_value = mock_reader

        # Mock image conversion
        mock_image = MagicMock()
        mock_convert.return_value = [mock_image]

        # Setup processor with mocked client
        with patch('document_processor.anthropic.Anthropic') as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            processor = DocumentProcessor(temp_db, "fake_api_key")

            # Process document
            doc_id = processor.process_document(sample_pdf_path)

        # Verify document was created
        assert doc_id is not None
        doc = temp_db.get_document(doc_id)
        assert doc is not None
        assert doc['total_pages'] == 5

        # Verify pages were added
        pages = temp_db.get_pages(doc_id)
        assert len(pages) == 5

        # Verify summaries were generated
        for page in pages:
            assert page['summdesc'] is not None

        # Verify document has summary
        assert doc['summdesc'] is not None

        # Verify significant pages were marked
        sig_pages = temp_db.get_legally_significant_pages(doc_id)
        assert len(sig_pages) > 0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_page_text(self, temp_db):
        """Test handling pages with no extractable text."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        # Add page with empty text
        page_id = temp_db.add_page(
            doc_id=doc_id,
            page_num=1,
            page_text="",
            page_image=b"image_data",
            summdesc="Page with no text"
        )

        assert page_id is not None

        pages = temp_db.get_pages(doc_id)
        assert pages[0]['page_text'] == ""

    def test_large_page_image(self, temp_db):
        """Test handling large page images."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        # Create a large fake image (1MB)
        large_image = b"x" * (1024 * 1024)

        page_id = temp_db.add_page(
            doc_id=doc_id,
            page_num=1,
            page_text="Text",
            page_image=large_image,
            summdesc="Page with large image"
        )

        assert page_id is not None

        # Verify we can retrieve it
        pages = temp_db.get_pages(doc_id)
        assert len(pages[0]['page_image']) == 1024 * 1024

    def test_unicode_in_document_text(self, temp_db):
        """Test handling unicode characters in document text."""
        doc_id = temp_db.add_document("test.pdf", "/path/test.pdf", "hash")

        unicode_text = "Contract with émployer 合同 אמנה"

        page_id = temp_db.add_page(
            doc_id=doc_id,
            page_num=1,
            page_text=unicode_text,
            page_image=b"img",
            summdesc="Unicode test"
        )

        pages = temp_db.get_pages(doc_id)
        assert pages[0]['page_text'] == unicode_text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
