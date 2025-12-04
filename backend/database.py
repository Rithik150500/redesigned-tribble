# database.py
import sqlite3
from pathlib import Path
from typing import Optional
import json

class LegalDocumentDatabase:
    """
    Manages the database of legal documents and their analyzed pages.
    
    This database stores three types of information:
    1. The original documents and their high-level summaries
    2. Individual pages with their text, images, and summaries
    3. Metadata about legal significance for quick filtering
    """
    
    def __init__(self, db_path: str = "legal_documents.db"):
        """Initialize the database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # This lets us access columns by name
        self._create_tables()
    
    def _create_tables(self):
        """
        Create the database schema.
        
        We're creating two main tables with a one-to-many relationship:
        documents -> pages. Each document can have many pages, but each page
        belongs to exactly one document.
        """
        cursor = self.conn.cursor()
        
        # The documents table stores high-level information about each document
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                filepath TEXT NOT NULL,
                summdesc TEXT,  -- The 2-3 sentence summary of the entire document
                total_pages INTEGER,
                legally_significant_pages INTEGER,  -- Count for quick reference
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_hash TEXT  -- To detect if the same file is uploaded again
            )
        """)
        
        # The pages table stores detailed information about each page
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                page_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                page_num INTEGER NOT NULL,
                summdesc TEXT,  -- The one-sentence summary of this page
                page_text TEXT,  -- The extracted text content
                page_image BLOB,  -- The page rendered as an image, stored as binary
                legally_significant INTEGER DEFAULT 0,  -- Boolean: 0 or 1
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id),
                UNIQUE(doc_id, page_num)  -- Ensure we don't duplicate pages
            )
        """)
        
        # Create indexes for faster querying
        # We'll often filter by legally_significant and look up by doc_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pages_doc_id 
            ON pages(doc_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pages_legally_significant 
            ON pages(doc_id, legally_significant)
        """)
        
        self.conn.commit()
    
    def add_document(self, filename: str, filepath: str, file_hash: str) -> int:
        """
        Add a new document to the database.
        
        Returns the doc_id of the newly created document.
        This is called when we first encounter a PDF file.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO documents (filename, filepath, file_hash)
            VALUES (?, ?, ?)
        """, (filename, filepath, file_hash))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_page(self, doc_id: int, page_num: int, page_text: str, 
                 page_image: bytes, summdesc: str = None):
        """
        Add a page to the database.
        
        This is called for each page as we process a document.
        We store both the text and image representation.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO pages (doc_id, page_num, page_text, page_image, summdesc)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, page_num, page_text, page_image, summdesc))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_document_summary(self, doc_id: int, summdesc: str, 
                               legally_significant_pages: list[int]):
        """
        Update the document with its summary and mark legally significant pages.
        
        This is called after we've processed all pages and generated the
        document-level summary. We also mark which pages are legally significant.
        """
        cursor = self.conn.cursor()
        
        # Update the document summary
        cursor.execute("""
            UPDATE documents 
            SET summdesc = ?, legally_significant_pages = ?
            WHERE doc_id = ?
        """, (summdesc, len(legally_significant_pages), doc_id))
        
        # Mark legally significant pages
        if legally_significant_pages:
            placeholders = ','.join('?' * len(legally_significant_pages))
            cursor.execute(f"""
                UPDATE pages 
                SET legally_significant = 1
                WHERE doc_id = ? AND page_num IN ({placeholders})
            """, [doc_id] + legally_significant_pages)
        
        self.conn.commit()
    
    def get_document(self, doc_id: int) -> Optional[dict]:
        """Retrieve a document's metadata."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM documents WHERE doc_id = ?
        """, (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_documents(self) -> list[dict]:
        """Get all documents with their summaries."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT doc_id, filename, summdesc, total_pages, 
                   legally_significant_pages
            FROM documents
            ORDER BY filename
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_pages(self, doc_id: int, page_nums: list[int] = None) -> list[dict]:
        """
        Get pages for a document.
        
        If page_nums is provided, get only those pages.
        Otherwise, get all pages.
        """
        cursor = self.conn.cursor()
        
        if page_nums:
            placeholders = ','.join('?' * len(page_nums))
            cursor.execute(f"""
                SELECT page_id, page_num, summdesc, page_text, 
                       page_image, legally_significant
                FROM pages
                WHERE doc_id = ? AND page_num IN ({placeholders})
                ORDER BY page_num
            """, [doc_id] + page_nums)
        else:
            cursor.execute("""
                SELECT page_id, page_num, summdesc, page_text, 
                       page_image, legally_significant
                FROM pages
                WHERE doc_id = ?
                ORDER BY page_num
            """, (doc_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_legally_significant_pages(self, doc_id: int) -> list[dict]:
        """Get only the legally significant pages for a document."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT page_id, page_num, summdesc, page_text, legally_significant
            FROM pages
            WHERE doc_id = ? AND legally_significant = 1
            ORDER BY page_num
        """, (doc_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
