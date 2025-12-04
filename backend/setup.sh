#!/bin/bash
# Legal Risk Analysis System - Backend Setup Script

set -e  # Exit on error

echo "========================================="
echo "Legal Risk Analysis System - Backend Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

if ! python3 -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null; then
    echo "Error: Python 3.10 or higher is required"
    exit 1
fi

# Check for system dependencies
echo ""
echo "Checking system dependencies..."

# Check for poppler (required for pdf2image)
if ! command -v pdftoppm &> /dev/null; then
    echo "Warning: poppler-utils not found."
    echo "Please install it for PDF processing:"
    echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  macOS: brew install poppler"
    echo "  Windows: Download from https://blog.alivate.com.au/poppler-windows/"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p data/documents
mkdir -p data/uploads
mkdir -p logs

# Copy environment template
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your ANTHROPIC_API_KEY"
else
    echo ""
    echo ".env file already exists, skipping..."
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from database import LegalDocumentDatabase; db = LegalDocumentDatabase(); db.close(); print('✓ Database initialized')"

echo ""
echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your ANTHROPIC_API_KEY"
echo "2. Add PDF documents to backend/data/documents/"
echo "3. Run: python scripts/ingest_documents.py"
echo "4. Test the MCP server: python tests/test_mcp_server.py"
echo "5. Start the web server: uvicorn web_server:app --reload"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
