# legal_doc_mcp_server.py
from mcp.server.fastmcp import FastMCP
from database import LegalDocumentDatabase
import base64
from typing import Optional
import os

# Initialize the FastMCP server
# FastMCP uses Python type hints and docstrings to automatically generate
# tool definitions, making it easy to create well-documented MCP tools
mcp = FastMCP("legal-document-analysis")

# Initialize database connection
# We'll use a global database instance that all tools can access
# In production, you might want dependency injection or connection pooling
db = LegalDocumentDatabase()

@mcp.tool()
async def list_documents() -> str:
    """
    List all available legal documents in the data room.
    
    Returns a formatted summary of each document including:
    - Document ID (for use in other tools)
    - Filename
    - Document summary
    - Total page count
    - Number of legally significant pages
    
    This tool helps you understand what documents are available before
    conducting detailed analysis. Use this first to plan your investigation.
    """
    try:
        # Query the database for all documents
        documents = db.get_all_documents()
        
        if not documents:
            return "No documents found in the data room. Please ensure documents have been processed and added to the database."
        
        # Format the response for maximum agent comprehension
        # We want to give enough detail for decision-making but not overwhelm
        result_lines = [
            "=== LEGAL DOCUMENTS DATA ROOM ===",
            f"\nTotal Documents: {len(documents)}\n"
        ]
        
        for doc in documents:
            # Build a rich description for each document
            # The agent needs to understand: what is this, how big is it, and what's important
            doc_info = [
                f"📄 Document ID: {doc['doc_id']}",
                f"   Filename: {doc['filename']}",
                f"   Summary: {doc['summdesc'] or 'No summary available'}",
                f"   Pages: {doc['total_pages']} total, {doc['legally_significant_pages']} legally significant",
                ""  # Empty line for readability
            ]
            result_lines.extend(doc_info)
        
        result_lines.append(
            "\nTo analyze a document in detail, use the get_documents tool with the document ID."
        )
        
        return "\n".join(result_lines)
        
    except Exception as e:
        # Always provide useful error messages to the agent
        # The agent needs to understand what went wrong and how to proceed
        return f"Error listing documents: {str(e)}\nPlease check that the database is accessible and properly configured."


@mcp.tool()
async def get_documents(doc_ids: list[int]) -> str:
    """
    Get detailed content for one or more documents.
    
    This tool provides rich, multi-layered access to documents:
    1. All page summaries in order (showing document structure)
    2. Full text of all legally significant pages (immediate access to key content)
    
    This design lets you understand both the document's organization and its
    most important content without needing to request hundreds of pages individually.
    
    Args:
        doc_ids: List of document IDs to retrieve (from list_documents)
    
    Returns:
        Formatted document content with page summaries and significant page text
    """
    try:
        if not doc_ids:
            return "Error: doc_ids parameter is required. Please provide at least one document ID."
        
        results = []
        
        for doc_id in doc_ids:
            # Get document metadata
            doc = db.get_document(doc_id)
            
            if not doc:
                results.append(f"\n❌ Document ID {doc_id} not found.")
                continue
            
            # Build the document response in layers
            doc_sections = [
                f"\n{'='*70}",
                f"DOCUMENT: {doc['filename']} (ID: {doc_id})",
                f"{'='*70}",
                f"\nSUMMARY: {doc['summdesc']}",
                f"PAGES: {doc['total_pages']} total, {doc['legally_significant_pages']} legally significant\n"
            ]
            
            # Layer 1: All page summaries (structure and navigation)
            doc_sections.append("\n--- PAGE SUMMARIES (Document Structure) ---\n")
            
            all_pages = db.get_pages(doc_id)
            
            if all_pages:
                for page in all_pages:
                    # Mark legally significant pages visually
                    marker = "⚖️ " if page['legally_significant'] else "   "
                    doc_sections.append(
                        f"{marker}Page {page['page_num']}: {page['summdesc']}"
                    )
            else:
                doc_sections.append("No pages found for this document.")
            
            # Layer 2: Full text of legally significant pages
            # This is the key intelligence - we automatically surface the most important content
            significant_pages = db.get_legally_significant_pages(doc_id)
            
            if significant_pages:
                doc_sections.append(
                    f"\n--- LEGALLY SIGNIFICANT PAGE CONTENT ---\n"
                    f"The following {len(significant_pages)} pages contain important legal provisions:\n"
                )
                
                for page in significant_pages:
                    doc_sections.extend([
                        f"\n{'─'*70}",
                        f"PAGE {page['page_num']}: {page['summdesc']}",
                        f"{'─'*70}\n",
                        page['page_text'] or "[No text extracted from this page]",
                        ""
                    ])
            else:
                doc_sections.append(
                    "\n--- LEGALLY SIGNIFICANT PAGE CONTENT ---\n"
                    "No pages were marked as legally significant in this document.\n"
                    "Use get_page_text to examine specific pages if needed."
                )
            
            results.append("\n".join(doc_sections))
        
        # Add usage guidance at the end
        results.append(
            "\n" + "="*70 + "\n"
            "ANALYSIS NOTES:\n"
            "- Pages marked with ⚖️ contain legally significant provisions\n"
            "- Use get_page_text for additional pages not marked as significant\n"
            "- Use get_page_image (limited use) to examine visual layout if needed\n"
        )
        
        return "\n\n".join(results)
        
    except Exception as e:
        return f"Error retrieving documents: {str(e)}\nPlease verify the document IDs and database connectivity."


@mcp.tool()
async def get_page_text(doc_id: int, page_nums: list[int]) -> str:
    """
    Get the full text content of specific pages.
    
    Use this tool when you need to examine pages that weren't marked as
    legally significant, or when you want to see context around significant
    pages (e.g., pages immediately before/after an important clause).
    
    Args:
        doc_id: The document ID (from list_documents)
        page_nums: List of page numbers to retrieve (1-indexed)
    
    Returns:
        Full text content of the requested pages
    """
    try:
        if not page_nums:
            return "Error: page_nums parameter is required. Please provide at least one page number."
        
        # Get document info for context
        doc = db.get_document(doc_id)
        if not doc:
            return f"Error: Document ID {doc_id} not found."
        
        # Validate page numbers
        if any(p < 1 or p > doc['total_pages'] for p in page_nums):
            return f"Error: Invalid page numbers. Document has {doc['total_pages']} pages. Requested pages: {page_nums}"
        
        # Retrieve the pages
        pages = db.get_pages(doc_id, page_nums)
        
        if not pages:
            return f"Error: Could not retrieve pages {page_nums} from document {doc_id}."
        
        # Format response
        result_lines = [
            f"{'='*70}",
            f"DOCUMENT: {doc['filename']} (ID: {doc_id})",
            f"REQUESTED PAGES: {', '.join(map(str, page_nums))}",
            f"{'='*70}\n"
        ]
        
        for page in pages:
            result_lines.extend([
                f"{'─'*70}",
                f"PAGE {page['page_num']}: {page['summdesc']}",
                f"{'─'*70}\n",
                page['page_text'] or "[No text extracted from this page]",
                ""
            ])
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error retrieving page text: {str(e)}"


@mcp.tool()
async def get_page_image(doc_id: int, page_nums: list[int]) -> str:
    """
    Get page images for visual analysis.
    
    ⚠️ LIMITED USE TOOL - Use sparingly as images consume significant tokens.
    
    Use this tool ONLY when:
    - Visual layout is important (tables, charts, diagrams)
    - You need to verify signature blocks or handwritten annotations
    - Text extraction seems incomplete or unclear
    - You need to understand document formatting or structure
    
    Try to exhaust text-based analysis before requesting images.
    
    Args:
        doc_id: The document ID (from list_documents)
        page_nums: List of page numbers to retrieve (1-indexed)
    
    Returns:
        Page images in base64 format with context information
    """
    try:
        if not page_nums:
            return "Error: page_nums parameter is required. Please provide at least one page number."
        
        # Get document info
        doc = db.get_document(doc_id)
        if not doc:
            return f"Error: Document ID {doc_id} not found."
        
        # Validate page numbers
        if any(p < 1 or p > doc['total_pages'] for p in page_nums):
            return f"Error: Invalid page numbers. Document has {doc['total_pages']} pages. Requested pages: {page_nums}"
        
        # Retrieve the pages
        pages = db.get_pages(doc_id, page_nums)
        
        if not pages:
            return f"Error: Could not retrieve pages {page_nums} from document {doc_id}."
        
        # Build response with images
        # Note: We return formatted text that describes what we're sending
        # The actual image data will be in the tool response content
        result_lines = [
            f"{'='*70}",
            f"DOCUMENT: {doc['filename']} (ID: {doc_id})",
            f"PAGE IMAGES RETRIEVED: {', '.join(map(str, page_nums))}",
            f"{'='*70}\n",
            "⚠️ USAGE NOTE: Images consume significant tokens. You have used this tool for:",
            f"   - Document {doc_id}: {len(page_nums)} pages\n"
        ]
        
        for page in pages:
            result_lines.extend([
                f"{'─'*70}",
                f"PAGE {page['page_num']}: {page['summdesc']}",
                f"{'─'*70}"
            ])
            
            # Convert image bytes to base64 for transmission
            if page['page_image']:
                image_b64 = base64.b64encode(page['page_image']).decode('utf-8')
                result_lines.append(f"\n[Image data: {len(image_b64)} bytes encoded]\n")
                # In a real implementation, you might return this in a structured format
                # that Claude can process as an actual image
            else:
                result_lines.append("\n[No image available for this page]\n")
        
        result_lines.extend([
            "",
            "TIP: Use get_page_text first for text-based analysis before requesting images.",
            "Reserve images for cases where visual layout is critical to understanding."
        ])
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error retrieving page images: {str(e)}"


# Server initialization and startup
def main():
    """
    Run the MCP server.
    
    This server uses stdio transport, which means it communicates via
    standard input/output. This is ideal for local MCP servers that will
    be launched by MCP hosts like Claude Desktop or custom applications.
    """
    import asyncio
    
    # Run the server
    # The server will listen on stdin/stdout for JSON-RPC messages
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
