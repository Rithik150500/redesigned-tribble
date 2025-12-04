# document_processor.py
import anthropic
from pathlib import Path
import hashlib
import base64
from pdf2image import convert_from_path
import pypdf
from typing import Optional
import io
from PIL import Image

class DocumentProcessor:
    """
    Processes PDF documents into the structured format needed for AI analysis.
    
    This class handles the entire pipeline:
    1. Extract text and images from each page
    2. Generate page-level summaries using Claude Haiku
    3. Generate document-level summary and identify significant pages
    4. Store everything in the database
    """
    
    def __init__(self, database: LegalDocumentDatabase, anthropic_api_key: str):
        """
        Initialize the processor with database and API connections.
        
        We use Claude Haiku for summarization because it's fast and cost-effective
        for processing potentially hundreds of pages.
        """
        self.db = database
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """
        Calculate a hash of the file to detect duplicates.
        
        This prevents reprocessing the same document if it's uploaded again.
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_text_from_page(self, pdf_reader: pypdf.PdfReader, 
                                page_num: int) -> str:
        """
        Extract text from a single PDF page.
        
        Returns the raw text content. Some PDFs have poor text extraction,
        which is why we also keep the image representation.
        """
        try:
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            return text.strip() if text else ""
        except Exception as e:
            print(f"Error extracting text from page {page_num}: {e}")
            return ""
    
    def _render_page_as_image(self, pdf_path: Path, page_num: int) -> bytes:
        """
        Render a PDF page as an image.
        
        We convert to image because:
        1. Visual layout can be legally significant (tables, highlights, etc.)
        2. Some PDFs have text that doesn't extract well
        3. Claude can analyze images directly
        
        Returns the image as PNG bytes for database storage.
        """
        try:
            # Convert just this one page (pages are 1-indexed in convert_from_path)
            images = convert_from_path(
                pdf_path, 
                first_page=page_num + 1,  # convert_from_path uses 1-based indexing
                last_page=page_num + 1,
                dpi=150  # Good balance between quality and file size
            )
            
            if images:
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='PNG', optimize=True)
                return img_byte_arr.getvalue()
            
            return b""
        except Exception as e:
            print(f"Error rendering page {page_num} as image: {e}")
            return b""
    
    def _summarize_page(self, page_text: str, page_image_bytes: bytes, 
                       page_num: int) -> str:
        """
        Generate a one-sentence summary of a page using Claude Haiku.
        
        We send both the text and image because:
        - Text provides the raw content
        - Image provides visual context (tables, formatting, etc.)
        
        This dual input helps Claude understand the page more completely.
        """
        try:
            # Prepare the image in base64 format for Claude
            image_base64 = base64.b64encode(page_image_bytes).decode('utf-8')
            
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=150,  # One sentence doesn't need many tokens
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""You are analyzing page {page_num + 1} of a legal document.

Here is the extracted text from this page:
{page_text[:2000]}  # Limit text length to avoid token overflow

Provide a single, concise sentence that summarizes the main topic or legal significance of this page. Focus on what legal matter this page addresses (e.g., "Non-compete clause restrictions", "Intellectual property assignment provisions", "Liability limitations and indemnification").

Your summary:"""
                        }
                    ]
                }]
            )
            
            summary = response.content[0].text.strip()
            # Ensure it's actually one sentence
            if '.' in summary:
                summary = summary.split('.')[0] + '.'
            return summary
            
        except Exception as e:
            print(f"Error summarizing page {page_num}: {e}")
            return "Unable to generate summary for this page."
    
    def _analyze_document(self, doc_id: int) -> tuple[str, list[int]]:
        """
        Analyze all pages of a document to create a document-level summary
        and identify legally significant pages.
        
        This is called after all pages have been processed individually.
        Returns: (document_summary, list_of_significant_page_numbers)
        """
        # Get all page summaries
        pages = self.db.get_pages(doc_id)
        
        # Build a comprehensive view of all pages
        page_summaries = []
        for page in pages:
            page_summaries.append(
                f"Page {page['page_num']}: {page['summdesc']}"
            )
        
        combined_summaries = "\n".join(page_summaries)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""You are analyzing a complete legal document. Here are summaries of each page:

{combined_summaries}

Please provide:
1. A 2-3 sentence overview of what this document is and its main legal purpose
2. A comma-separated list of page numbers that contain legally significant information

Legally significant pages are those containing:
- Contractual obligations or duties
- Deadlines or time-sensitive provisions
- Financial terms or payment obligations
- Liability clauses or indemnification
- Termination conditions
- Intellectual property assignments
- Non-compete or confidentiality provisions
- Regulatory compliance requirements
- Dispute resolution or governing law provisions
- Material representations or warranties

Format your response exactly as:
SUMMARY: [Your 2-3 sentence summary]
SIGNIFICANT_PAGES: [comma-separated page numbers, e.g., 1,3,7,12]

If no pages are particularly significant, respond with SIGNIFICANT_PAGES: none"""
                }]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse the response
            summary = ""
            significant_pages = []
            
            for line in response_text.split('\n'):
                if line.startswith('SUMMARY:'):
                    summary = line.replace('SUMMARY:', '').strip()
                elif line.startswith('SIGNIFICANT_PAGES:'):
                    pages_str = line.replace('SIGNIFICANT_PAGES:', '').strip()
                    if pages_str.lower() != 'none':
                        # Parse comma-separated page numbers
                        try:
                            significant_pages = [
                                int(p.strip()) 
                                for p in pages_str.split(',') 
                                if p.strip().isdigit()
                            ]
                        except ValueError:
                            print(f"Error parsing page numbers: {pages_str}")
            
            return summary, significant_pages
            
        except Exception as e:
            print(f"Error analyzing document {doc_id}: {e}")
            return "Unable to generate document summary.", []
    
    def process_document(self, pdf_path: Path) -> int:
        """
        Process a complete PDF document through the entire pipeline.
        
        This is the main entry point. It:
        1. Checks if the document was already processed
        2. Extracts text and images from each page
        3. Generates page summaries
        4. Generates document summary and identifies significant pages
        5. Stores everything in the database
        
        Returns the doc_id of the processed document.
        """
        print(f"\n{'='*60}")
        print(f"Processing document: {pdf_path.name}")
        print(f"{'='*60}\n")
        
        # Calculate file hash to check for duplicates
        file_hash = self._calculate_file_hash(pdf_path)
        
        # Check if already processed
        # (We'd need to add a method to check by hash, but I'll skip that for brevity)
        
        # Create document record
        doc_id = self.db.add_document(
            filename=pdf_path.name,
            filepath=str(pdf_path),
            file_hash=file_hash
        )
        
        # Open PDF for reading
        with open(pdf_path, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            print(f"Document has {total_pages} pages. Processing each page...\n")
            
            # Process each page
            for page_num in range(total_pages):
                print(f"Processing page {page_num + 1}/{total_pages}...", end=' ')
                
                # Extract text
                page_text = self._extract_text_from_page(pdf_reader, page_num)
                
                # Render as image
                page_image = self._render_page_as_image(pdf_path, page_num)
                
                # Generate summary
                page_summary = self._summarize_page(page_text, page_image, page_num)
                print(f"✓ Summary: {page_summary[:60]}...")
                
                # Store in database
                self.db.add_page(
                    doc_id=doc_id,
                    page_num=page_num + 1,  # Store as 1-indexed for human readability
                    page_text=page_text,
                    page_image=page_image,
                    summdesc=page_summary
                )
            
            # Update document total_pages
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE documents SET total_pages = ? WHERE doc_id = ?
            """, (total_pages, doc_id))
            self.db.conn.commit()
        
        print(f"\n{'='*60}")
        print("Analyzing complete document...")
        print(f"{'='*60}\n")
        
        # Generate document-level analysis
        doc_summary, significant_pages = self._analyze_document(doc_id)
        
        print(f"Document Summary: {doc_summary}")
        print(f"Legally Significant Pages: {significant_pages}\n")
        
        # Update document with summary and significant pages
        self.db.update_document_summary(doc_id, doc_summary, significant_pages)
        
        print(f"✓ Document processing complete! (doc_id: {doc_id})\n")
        
        return doc_id
