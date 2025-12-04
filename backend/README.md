# Legal Risk Analysis System - Backend

This is the backend service for the Legal Risk Analysis System, providing document processing, AI agent orchestration, and real-time communication with the frontend.

## Architecture Overview

The backend is organized into four layers:

```
┌─────────────────────────────────────────────┐
│          Web Interface Layer                │
│  (FastAPI + WebSocket + REST API)          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Agent Orchestration Layer           │
│    (Deep Agents + LangGraph + Human-in-     │
│              the-Loop)                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         MCP Document Analysis Layer         │
│   (Tools for document access & analysis)    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      Document Processing & Database         │
│    (PDF processing + SQLite storage)        │
└─────────────────────────────────────────────┘
```

## Components

### Layer 1: Document Processing & Database

**Files**: `document_processor.py`, `database.py`

- **document_processor.py**: Handles PDF ingestion
  - Extracts text and renders images for each page
  - Uses Claude Haiku to generate page-level summaries
  - Identifies legally significant pages
  - Generates document-level summaries

- **database.py**: SQLite database schema and ORM
  - `documents` table: Metadata and summaries
  - `pages` table: Page content, images, and significance markers
  - Optimized indexes for quick retrieval

### Layer 2: MCP Document Analysis Server

**File**: `legal_doc_mcp_server.py`

Provides four MCP tools:

1. **list_documents**: Browse available documents
2. **get_documents**: Access document content with summaries
3. **get_page_text**: Retrieve specific page text
4. **get_page_image**: Get page images (limited use)

The server uses FastMCP for automatic tool definition generation from Python functions.

### Layer 3: Agent Orchestration

**Directory**: `agents/`

- **main_agent.py**: Strategic coordinator
  - Creates analysis plans
  - Delegates to subagents
  - Manages findings and synthesis

- **analysis_subagent.py**: Document investigator
  - Conducts focused investigations
  - Has access to MCP tools and web search
  - Can be invoked multiple times

- **report_subagent.py**: Final report generator
  - Synthesizes all findings
  - Creates comprehensive risk report
  - Single-use only

- **mcp_integration.py**: MCP client integration
  - Connects agents to MCP server
  - Manages stdio transport

### Layer 4: Web Interface

**File**: `web_server.py`

- REST API endpoints:
  - `POST /api/sessions`: Create analysis session
  - `GET /api/documents`: List documents
  - `GET /api/documents/{id}`: Get document details
  - `POST /api/upload`: Upload new documents

- WebSocket endpoint:
  - `WS /ws/{session_id}`: Real-time agent communication
  - Human-in-the-loop approval workflow
  - Progress updates and messaging

## Setup

### Prerequisites

- Python 3.10 or higher
- poppler-utils (for PDF processing)
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - macOS: `brew install poppler`
  - Windows: Download from https://blog.alivate.com.au/poppler-windows/

### Installation

```bash
# Run the setup script
cd backend
chmod +x setup.sh
./setup.sh

# Or manual installation:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`
2. Add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```

### Database Initialization

The database is automatically created on first run. To manually initialize:

```bash
python3 -c "from database import LegalDocumentDatabase; LegalDocumentDatabase().close()"
```

## Usage

### 1. Ingest Documents

Place PDF files in `data/documents/` and run:

```bash
python scripts/ingest_documents.py
```

This will:
- Process each PDF page-by-page
- Generate summaries using Claude Haiku
- Identify legally significant pages
- Store everything in the database

### 2. Test the MCP Server

```bash
python tests/test_mcp_server.py
```

This verifies that document analysis tools are working correctly.

### 3. Test the Agent System (Command-Line)

```bash
python scripts/run_analysis.py
```

This runs a complete analysis with command-line approval prompts, allowing you to test the agent workflow without the web UI.

### 4. Start the Web Server

```bash
uvicorn web_server:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/{session_id}

## Development Workflow

### Adding Documents

1. Place PDFs in `data/documents/`
2. Run `python scripts/ingest_documents.py`
3. Check database: `python -c "from database import LegalDocumentDatabase; db = LegalDocumentDatabase(); print(db.get_all_documents())"`

### Testing the MCP Layer

```bash
# Test individual tools
python tests/test_mcp_server.py

# Or use the MCP inspector
mcp dev legal_doc_mcp_server.py
```

### Testing the Agent Layer

```bash
# Command-line testing with human approvals
python scripts/run_analysis.py

# Full integration test
python tests/test_agent_system.py
```

### Testing the Web Layer

```bash
# Start server
uvicorn web_server:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/api/documents
```

## API Reference

### REST Endpoints

#### Create Session
```http
POST /api/sessions
Response: {"session_id": "uuid"}
```

#### List Documents
```http
GET /api/documents
Response: {
  "documents": [
    {
      "doc_id": 1,
      "filename": "contract.pdf",
      "summdesc": "Employment agreement...",
      "total_pages": 10,
      "legally_significant_pages": 3
    }
  ]
}
```

#### Get Document
```http
GET /api/documents/{doc_id}
Response: {
  "doc_id": 1,
  "filename": "contract.pdf",
  "summdesc": "...",
  "pages": [...]
}
```

#### Upload Document
```http
POST /api/upload
Content-Type: multipart/form-data
Body: file=<PDF file>
Response: {"doc_id": 2, "filename": "new.pdf"}
```

### WebSocket Protocol

#### Connect
```javascript
ws://localhost:8000/ws/{session_id}
```

#### Messages from Client
```json
{
  "type": "start_analysis",
  "message": "Analyze all contracts for IP assignment clauses"
}
```

```json
{
  "type": "approval_decision",
  "decisions": [
    {"action_id": "uuid", "decision": "approve"}
  ]
}
```

#### Messages from Server
```json
{
  "type": "analysis_started",
  "message": "Starting analysis..."
}
```

```json
{
  "type": "agent_message",
  "content": "Found 3 employment agreements..."
}
```

```json
{
  "type": "approval_required",
  "actions": [
    {
      "action_id": "uuid",
      "tool_name": "write_file",
      "context": {...}
    }
  ]
}
```

```json
{
  "type": "analysis_complete",
  "message": "Analysis finished",
  "result": {...}
}
```

## Database Schema

### documents Table
```sql
CREATE TABLE documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    filepath TEXT NOT NULL,
    summdesc TEXT,
    total_pages INTEGER,
    legally_significant_pages INTEGER,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash TEXT
);
```

### pages Table
```sql
CREATE TABLE pages (
    page_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    page_num INTEGER NOT NULL,
    summdesc TEXT,
    page_text TEXT,
    page_image BLOB,
    legally_significant INTEGER DEFAULT 0,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id),
    UNIQUE(doc_id, page_num)
);
```

## Troubleshooting

### "Module not found" errors

Make sure you've activated the virtual environment:
```bash
source venv/bin/activate
```

### PDF processing fails

Install poppler-utils:
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### Database locked errors

SQLite doesn't handle concurrent writes well. Use `check_same_thread=False` (already configured) or upgrade to PostgreSQL for production.

### Agent doesn't have access to documents

Verify the MCP server path in agent configuration and ensure documents are ingested.

### WebSocket connection fails

Check CORS settings in `web_server.py` and ensure the frontend URL is allowed.

## Production Deployment

### Security Checklist

- [ ] Change CORS settings to restrict origins
- [ ] Add authentication to API endpoints
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/WSS
- [ ] Add rate limiting
- [ ] Sanitize file uploads
- [ ] Add logging and monitoring

### Recommended Stack

- **Database**: PostgreSQL with connection pooling
- **Web Server**: Gunicorn + Uvicorn workers
- **Reverse Proxy**: Nginx
- **Process Manager**: systemd or supervisor
- **Monitoring**: Prometheus + Grafana

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/legal-analysis/issues
- Documentation: See main README.md
