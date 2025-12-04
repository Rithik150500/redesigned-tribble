# agents/analysis_subagent.py
"""
Analysis Subagent for Deep Document Investigation

This subagent receives focused assignments from the main agent and conducts
detailed investigation of specific legal issues or document types.
"""

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
import anthropic
import os

# System prompt for Analysis subagent
ANALYSIS_SUBAGENT_PROMPT = """You are a specialized legal analyst conducting detailed document investigation.

CURRENT ASSIGNMENT:
{assignment}

YOUR APPROACH:
1. Start with list_documents to understand what's available
2. Identify documents relevant to your assignment based on their summaries
3. Use get_documents to retrieve relevant documents
   - This gives you page summaries (document structure) 
   - Plus full text of legally significant pages automatically
4. Analyze the content carefully for your assigned focus
5. Use get_page_text if you need additional pages beyond those marked significant
6. Use get_page_image SPARINGLY - only when visual layout is critical
7. Use web_search to research legal standards or precedents
8. Document your findings in organized files

WHAT TO LOOK FOR:
- Specific obligations and duties
- Deadlines and time-sensitive provisions
- Financial terms and payment obligations
- Liability clauses and indemnification
- Termination conditions and consequences
- Intellectual property provisions
- Non-compete and confidentiality requirements
- Regulatory compliance requirements
- Dispute resolution mechanisms
- Material representations and warranties
- Unusual or problematic clauses
- Inconsistencies across documents

ANALYSIS QUALITY:
- Be thorough and detail-oriented
- Quote specific language from documents (with page numbers)
- Identify patterns across multiple documents
- Note any missing or concerning provisions
- Research legal standards for questionable clauses
- Assess risk levels (High/Medium/Low)
- Provide context about why something matters

DOCUMENTATION:
- Create clearly named files for your findings
- Use descriptive filenames: /analysis/employment_agreements_findings.md
- Structure your findings logically
- Include document names and page numbers for every finding
- Write clear, professional analysis

Remember: Your findings will be used by the main agent to create the final report.
Be thorough, accurate, and well-organized."""


def create_analysis_subagent(
    anthropic_api_key: str = None,
    mcp_server_path: str = "./legal_doc_mcp_server.py"
):
    """
    Create an Analysis subagent for detailed document investigation.
    
    This subagent is created fresh for each investigation task,
    conducts focused analysis, and returns findings to the main agent.
    
    Args:
        anthropic_api_key: API key for Claude
        mcp_server_path: Path to the MCP server for document access
    
    Returns:
        Configured Analysis subagent
    """
    
    if anthropic_api_key is None:
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Note: We'll configure this subagent with MCP tools when we integrate
    # For now, this shows the structure
    
    agent = create_deep_agent(
        model="claude-sonnet-4-5-20250929",
        system_prompt=ANALYSIS_SUBAGENT_PROMPT,
        backend=lambda rt: StateBackend(rt),  # Ephemeral storage
        # Tools will be added when integrated with main agent
    )
    
    return agent
