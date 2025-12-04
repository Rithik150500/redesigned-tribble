# Legal Risk Analysis System

> A comprehensive AI-powered system for analyzing legal documents with human-in-the-loop oversight

This system provides collaborative legal document analysis by combining AI agents with human judgment. It processes PDF documents, extracts key information, and conducts strategic analysis while keeping humans in control of all significant operations.

## System Overview

The Legal Risk Analysis System is built on a layered architecture that can be developed and tested independently:

```
┌──────────────────────────────────────────────┐
│          Layer 4: Web Interface              │
│     (React Frontend + FastAPI Backend)       │
└──────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────┐
│      Layer 3: Agent Orchestration            │
│        (Deep Agents + LangGraph +            │
│         Human-in-the-Loop Approvals)         │
└──────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────┐
│    Layer 2: MCP Document Analysis Server     │
│   (Tools for document access & research)     │
└──────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────┐
│   Layer 1: Document Processing & Database    │
│      (PDF Extraction + SQLite Storage)       │
└──────────────────────────────────────────────┘
```

## Key Features

### Document Processing
- **PDF Ingestion**: Extract text and render images from PDF pages
- **AI Summarization**: Generate page-level and document-level summaries using Claude Haiku
- **Significance Detection**: Automatically identify legally significant pages
- **Structured Storage**: SQLite database with optimized indexes

### MCP Document Analysis
- **list_documents**: Browse available documents
- **get_documents**: Access full document content with summaries
- **get_page_text**: Retrieve specific pages
- **get_page_image**: Visual analysis of page layout (limited use)

### Deep Agent System
- **Main Agent**: Strategic coordinator that develops analysis plans
- **Analysis Subagent**: Conducts detailed document investigations
- **Report Subagent**: Synthesizes findings into comprehensive reports
- **Human-in-the-Loop**: All significant actions require explicit approval

### Web Interface
- **Three-Panel Layout**: Documents, workflow, and files
- **Real-Time Updates**: WebSocket communication
- **PDF Viewer**: Integrated document viewing with highlights
- **Approval Workflow**: Review and approve/reject agent actions
- **File Browser**: View generated analysis files

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 14+ (for frontend)
- poppler-utils (for PDF processing)
- Anthropic API key

### Backend Setup

```bash
cd backend
./setup.sh
# Edit .env and add your ANTHROPIC_API_KEY
source venv/bin/activate
```

### Frontend Setup

```bash
cd src
npm install
```

### Running the System

1. **Ingest Documents**:
```bash
cd backend
# Place PDFs in data/documents/
python scripts/ingest_documents.py
```

2. **Test Each Layer**:
```bash
# Test document processing
python -c "from database import LegalDocumentDatabase; print(LegalDocumentDatabase().get_all_documents())"

# Test MCP server
python tests/test_mcp_server.py

# Test agent system (command-line)
python scripts/run_analysis.py
```

3. **Start Full System**:
```bash
# Terminal 1: Backend
cd backend
uvicorn web_server:app --reload

# Terminal 2: Frontend
cd src
npm start
```

4. **Open Browser**: http://localhost:3000

## Development Approach

### Layer-by-Layer Development

This system is designed to be built incrementally:

#### 1. Start with Document Processing (Layer 1)

Get comfortable with the foundation:
```bash
cd backend
python scripts/ingest_documents.py
```

Verify documents are processed correctly:
- Check page summaries
- Review legally significant pages
- Inspect database content

#### 2. Build the MCP Server (Layer 2)

Test document access tools:
```bash
python tests/test_mcp_server.py
```

Or use MCP inspector:
```bash
mcp dev legal_doc_mcp_server.py
```

#### 3. Implement the Agent System (Layer 3)

Start with command-line testing:
```bash
python scripts/run_analysis.py
```

This lets you:
- Test agent logic without UI complexity
- Verify approval workflow
- Debug agent decision-making
- See filesystem interactions

#### 4. Build the Web Interface (Layer 4)

Finally, connect everything with the web UI:
```bash
# Start backend
uvicorn web_server:app --reload

# Start frontend
npm start
```

### Why This Approach Works

1. **Independent Testing**: Each layer can be tested in isolation
2. **Faster Iteration**: Debug issues in specific components
3. **Progressive Complexity**: Add UI only when core logic is solid
4. **Better Understanding**: See how each piece fits together

## Architecture Deep Dive

### Document Processing Pipeline

```python
# 1. PDF Ingestion
processor = DocumentProcessor(db, api_key)
doc_id = processor.process_document(pdf_path)

# 2. For each page:
#    - Extract text
#    - Render as image
#    - Generate one-sentence summary (Claude Haiku)
#    - Store in database

# 3. Document-level analysis:
#    - Review all page summaries
#    - Generate document summary
#    - Identify legally significant pages
```

### MCP Tool Design

The MCP server provides **layered access** to documents:

1. **High-level**: `list_documents` - Browse what's available
2. **Mid-level**: `get_documents` - Get summaries + significant pages
3. **Detailed**: `get_page_text` - Access specific pages
4. **Visual**: `get_page_image` - See layout (limited use)

This design minimizes token usage while providing comprehensive access.

### Agent Workflow

```
Main Agent:
├─ Creates analysis plan using write_todos
├─ Delegates investigations to Analysis Subagent
│  └─ Analysis Subagent:
│     ├─ Accesses documents via MCP tools
│     ├─ Conducts web research
│     ├─ Writes findings to files
│     └─ Returns summary to Main Agent
├─ Reviews findings, adjusts plan
├─ Delegates more investigations (repeat)
└─ Calls Report Subagent (once)
   └─ Report Subagent:
      ├─ Reads all analysis files
      ├─ Synthesizes findings
      └─ Generates final report
```

### Human-in-the-Loop Integration

The system interrupts for approval on:
- **Document access**: Before retrieving documents
- **File operations**: Before writing/editing files
- **Web searches**: Before conducting research
- **Subagent calls**: Before delegating to subagents

Each approval shows:
- What action the agent wants to perform
- Why it's needed (context)
- What data will be accessed or modified

Users can:
- **Approve**: Let it proceed
- **Edit**: Modify parameters
- **Reject**: Block the action

## Project Structure

```
legal-risk-analysis/
├── backend/                 # Backend services
│   ├── agents/             # Deep agent system
│   │   ├── main_agent.py
│   │   ├── analysis_subagent.py
│   │   ├── report_subagent.py
│   │   ├── mcp_integration.py
│   │   └── utils.py
│   ├── data/               # Document storage
│   │   ├── documents/      # Original PDFs
│   │   └── uploads/        # User uploads
│   ├── scripts/            # Utility scripts
│   │   ├── ingest_documents.py
│   │   └── run_analysis.py
│   ├── tests/              # Test scripts
│   │   ├── test_mcp_server.py
│   │   └── test_agent_system.py
│   ├── config.py           # Configuration
│   ├── database.py         # Database layer
│   ├── document_processor.py  # PDF processing
│   ├── legal_doc_mcp_server.py  # MCP server
│   ├── web_server.py       # FastAPI server
│   ├── requirements.txt    # Python dependencies
│   ├── setup.sh            # Setup script
│   └── README.md           # Backend docs
├── src/                    # React frontend
│   ├── components/         # UI components
│   │   ├── DocumentPanel.js
│   │   ├── WorkflowPanel.js
│   │   └── FilePanel.js
│   ├── services/           # Services
│   │   └── websocket.js
│   ├── App.js              # Main app
│   └── ...
├── CLAUDE.md               # AI assistant guide
├── README.md               # User-facing docs
└── QUICKSTART.md           # Quick start guide
```

## Configuration

### Environment Variables

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=your_key_here
LEGAL_DOC_DB_PATH=legal_documents.db
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:3000
```

### Database

SQLite by default. For production, consider PostgreSQL:

```python
# In database.py, replace SQLite connection with:
import psycopg2
conn = psycopg2.connect(DATABASE_URL)
```

## Testing Strategy

### Unit Tests
```bash
pytest backend/tests/
```

### Integration Tests
```bash
# Test full pipeline
python backend/scripts/ingest_documents.py
python backend/tests/test_mcp_server.py
python backend/tests/test_agent_system.py
```

### End-to-End Tests
```bash
# Start system and use browser
uvicorn web_server:app &
npm start &
# Open http://localhost:3000
```

## Deployment

### Docker

```bash
# Build backend
docker build -t legal-analysis-backend ./backend

# Build frontend
docker build -t legal-analysis-frontend ./src

# Run with docker-compose
docker-compose up
```

### Production Considerations

- [ ] Use PostgreSQL for database
- [ ] Enable HTTPS/WSS
- [ ] Add authentication (OAuth, JWT)
- [ ] Implement rate limiting
- [ ] Add logging and monitoring
- [ ] Use environment-based configuration
- [ ] Set up CI/CD pipeline

## Troubleshooting

### Common Issues

**"Module not found" errors**: Activate venv
```bash
source backend/venv/bin/activate
```

**PDF processing fails**: Install poppler
```bash
sudo apt-get install poppler-utils  # Ubuntu
brew install poppler  # macOS
```

**WebSocket won't connect**: Check CORS settings in `web_server.py`

**Agent has no documents**: Run `python scripts/ingest_documents.py`

## Philosophy: Collaborative Analysis

This system succeeds when AI and human work together effectively:

### The AI Provides:
- **Tireless investigation**: Review hundreds of pages without fatigue
- **Pattern recognition**: Identify similar clauses across documents
- **Research**: Look up relevant case law and regulations
- **Organization**: Structure findings systematically

### The Human Provides:
- **Judgment**: Decide what matters most
- **Strategic direction**: Guide the investigation focus
- **Oversight**: Approve sensitive operations
- **Context**: Apply business and legal knowledge

### The System Provides:
- **Transparency**: See what the AI is doing
- **Control**: Approve/reject all significant actions
- **Auditability**: Track all decisions and findings
- **Efficiency**: Faster than manual review, more thorough than quick scanning

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file

## Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - AI capabilities
- [Deep Agents](https://github.com/anthropics/deepagents) - Agent framework
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://reactjs.org/) - UI framework

## Support

- Documentation: See `/backend/README.md` and `/CLAUDE.md`
- Issues: GitHub Issues
- Questions: GitHub Discussions
