# ingest_documents.py
import os
from pathlib import Path
import time
from database import LegalDocumentDatabase
from document_processor import DocumentProcessor
import sys

def process_data_room(data_room_path: str, anthropic_api_key: str):
    """
    Process all PDF documents in a data room folder.
    
    This script finds all PDFs in the specified folder and processes them
    through our pipeline. You can run this whenever new documents are added.
    """
    data_room = Path(data_room_path)
    
    if not data_room.exists():
        print(f"Error: Data room folder '{data_room_path}' does not exist.")
        sys.exit(1)
    
    # Initialize database and processor
    db = LegalDocumentDatabase()
    processor = DocumentProcessor(db, anthropic_api_key)
    
    # Find all PDF files
    pdf_files = list(data_room.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_room_path}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF documents to process")
    print(f"{'='*60}\n")
    
    # Process each document
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[Document {i}/{len(pdf_files)}]")
        try:
            doc_id = processor.process_document(pdf_path)
            print(f"✓ Successfully processed: {pdf_path.name} (ID: {doc_id})")
        except Exception as e:
            print(f"✗ Error processing {pdf_path.name}: {e}")
            continue
    
    # Show summary
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}\n")
    
    all_docs = db.get_all_documents()
    print(f"Total documents in database: {len(all_docs)}")
    print("\nDocument Summary:")
    for doc in all_docs:
        print(f"\n{doc['filename']}:")
        print(f"  Pages: {doc['total_pages']}")
        print(f"  Legally significant pages: {doc['legally_significant_pages']}")
        print(f"  Summary: {doc['summdesc'][:100]}...")
    
    db.close()

if __name__ == "__main__":
    # You would typically read these from environment variables or config
    DATA_ROOM_PATH = os.getenv("DATA_ROOM_PATH", "./data_room")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    process_data_room(DATA_ROOM_PATH, ANTHROPIC_API_KEY)
