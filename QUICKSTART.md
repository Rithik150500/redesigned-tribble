# Quick Start Guide

Get the Legal Risk Analysis System up and running in 10 minutes.

## Prerequisites

Before you begin, make sure you have:

- [ ] Python 3.10 or higher installed
- [ ] Node.js 14+ and npm installed
- [ ] An Anthropic API key (get one at https://console.anthropic.com/)
- [ ] poppler-utils installed (for PDF processing)

### Installing poppler-utils

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows
# Download from: https://blog.alivate.com.au/poppler-windows/
```

## Step 1: Clone and Setup Backend (5 minutes)

```bash
# Clone the repository
git clone <repository-url>
cd redesigned-tribble

# Run the automated setup script
cd backend
./setup.sh

# The script will:
# - Check Python version
# - Create virtual environment
# - Install dependencies
# - Create directory structure
# - Initialize database
# - Create .env file
```

## Step 2: Configure API Key (30 seconds)

```bash
# Edit the .env file
nano .env

# Add your Anthropic API key:
ANTHROPIC_API_KEY=sk-ant-...your-key-here...

# Save and exit (Ctrl+X, Y, Enter)
```

## Step 3: Add Sample Documents (2 minutes)

```bash
# Option 1: Use your own PDFs
# Place PDF files in backend/data/documents/
cp /path/to/your/*.pdf backend/data/documents/

# Option 2: Create a simple test document
cd backend/data/documents
cat > test.txt << 'EOF'
This is a test legal document.
It will be processed to demonstrate the system.
EOF
# Note: The system works best with actual PDF files

# Process the documents
cd ../..
source venv/bin/activate
python scripts/ingest_documents.py
```

You should see output like:
```
==========================================================
Processing document: contract.pdf
==========================================================

Document has 10 pages. Processing each page...

Processing page 1/10... ✓ Summary: Introduction and definitions...
Processing page 2/10... ✓ Summary: Payment terms and schedule...
...

✓ Document processing complete! (doc_id: 1)
```

## Step 4: Test the System (1 minute)

### Test Document Processing

```bash
# Verify documents are in the database
python -c "from database import LegalDocumentDatabase; db = LegalDocumentDatabase(); print(f'Documents: {len(db.get_all_documents())}')"
```

### Test MCP Server

```bash
# Run the MCP server test
python tests/test_mcp_server.py
```

Expected output:
```
Testing MCP Server...
✓ list_documents working
✓ get_documents working
✓ get_page_text working
All tests passed!
```

### Test Agent System (Command-Line)

```bash
# Run a simple analysis without the UI
python scripts/run_analysis.py
```

This will:
1. Start the agent
2. Prompt for approval at each step
3. Show you the agent's decision-making process
4. Generate analysis files

## Step 5: Start the Web Interface (2 minutes)

### Terminal 1: Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn web_server:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
```

### Terminal 2: Frontend Development Server

```bash
cd src
npm install  # First time only
npm start
```

The frontend will open automatically at http://localhost:3000

## Step 6: Run Your First Analysis

1. **Open the Web Interface**: http://localhost:3000

2. **Wait for Connection**: You'll see "Connected" in the top-right

3. **Type Your Analysis Request** in the center panel:
   ```
   Please analyze all documents for liability and indemnification provisions
   ```

4. **Review and Approve Actions**:
   - The agent will request approval to access documents
   - Review what it wants to do
   - Click "Approve" to proceed

5. **Watch the Analysis**:
   - See the agent's thought process in real-time
   - Documents will be highlighted in the left panel
   - Generated files appear in the right panel

6. **Review Results**:
   - Click files in the right panel to view findings
   - Check the final report when analysis completes

## Common Issues and Solutions

### "ANTHROPIC_API_KEY not found"

**Solution**: Make sure you edited `backend/.env` and added your API key.

```bash
cd backend
cat .env  # Check if ANTHROPIC_API_KEY is set
```

### "No module named 'anthropic'"

**Solution**: Activate the virtual environment.

```bash
cd backend
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

### "poppler not found" or PDF processing fails

**Solution**: Install poppler-utils for your system (see Prerequisites above).

### "No documents found"

**Solution**: Run the document ingestion script.

```bash
cd backend
source venv/bin/activate
python scripts/ingest_documents.py
```

### Frontend won't connect to backend

**Solution**: Check that both servers are running:

```bash
# Check backend (should show Uvicorn output)
curl http://localhost:8000/api/documents

# Check frontend (should open browser)
# Make sure npm start is running
```

### "Database locked" errors

**Solution**: SQLite doesn't handle concurrent writes well. For production, use PostgreSQL. For development, restart the backend server.

## Next Steps

### Learn the System

- **Read the Architecture Guide**: See `PROJECT_README.md` for detailed architecture
- **Understand the Layers**: Each layer can be developed and tested independently
- **Explore Agent Prompts**: Check `backend/agents/main_agent.py` to see how agents work

### Customize the System

- **Add More Documents**: Place PDFs in `backend/data/documents/` and re-run ingestion
- **Modify Agent Behavior**: Edit system prompts in `backend/agents/`
- **Adjust Approval Rules**: Configure what requires approval in agent configs
- **Customize UI**: Modify React components in `src/components/`

### Production Deployment

- **Database**: Switch from SQLite to PostgreSQL
- **Security**: Add authentication and authorization
- **Scaling**: Use Gunicorn with multiple workers
- **Monitoring**: Add logging and error tracking
- **HTTPS**: Set up SSL certificates for secure connections

## Development Workflow

### Recommended Order

1. **Start with Document Processing**:
   - Get comfortable with ingesting documents
   - Understand how summaries are generated
   - Inspect the database

2. **Explore the MCP Layer**:
   - Test document access tools
   - Understand the layered access model
   - Try the MCP inspector: `mcp dev backend/legal_doc_mcp_server.py`

3. **Experiment with Agents**:
   - Run command-line analysis: `python scripts/run_analysis.py`
   - See how agents make decisions
   - Understand the approval workflow

4. **Build Your Features**:
   - Modify agent prompts for your use case
   - Add custom MCP tools
   - Enhance the UI

### Useful Commands

```bash
# Activate environment
source backend/venv/bin/activate

# Re-ingest documents after changes
python backend/scripts/ingest_documents.py

# Test MCP tools
python backend/tests/test_mcp_server.py

# Run command-line analysis
python backend/scripts/run_analysis.py

# Start backend with auto-reload
uvicorn backend.web_server:app --reload

# Start frontend dev server
cd src && npm start

# Check database contents
python -c "from backend.database import LegalDocumentDatabase; db = LegalDocumentDatabase(); [print(d) for d in db.get_all_documents()]"
```

## Getting Help

- **Documentation**: Check `PROJECT_README.md` and `backend/README.md`
- **AI Assistant Guide**: See `CLAUDE.md` for detailed technical docs
- **Issues**: Open a GitHub issue if you encounter problems
- **Examples**: Look in `backend/tests/` for working examples

## Success Checklist

After completing this quick start, you should have:

- [ ] Backend server running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] At least one document processed and in the database
- [ ] Successfully run a test analysis
- [ ] Seen the approval workflow in action
- [ ] Reviewed generated analysis files

Congratulations! You're now ready to use the Legal Risk Analysis System.

## What's Next?

- **Add Real Documents**: Process your actual legal documents
- **Customize Analysis**: Modify agent prompts for your specific needs
- **Explore Advanced Features**: Try different analysis strategies
- **Build Custom Tools**: Add new MCP tools for specialized analysis

Happy analyzing! 🎉
