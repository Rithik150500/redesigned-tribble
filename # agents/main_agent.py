# agents/main_agent.py
"""
Main Legal Risk Analysis Agent

This agent serves as the strategic coordinator for legal document analysis.
It develops analysis plans, delegates investigations to subagents, and ensures
comprehensive coverage of all legal risks.
"""

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
import anthropic
import os

# System prompt for the main agent
# This is crucial - it defines the agent's role, capabilities, and approach
MAIN_AGENT_SYSTEM_PROMPT = """You are a Legal Risk Analysis Expert coordinating a comprehensive review of company legal documents.

YOUR ROLE:
You are the senior legal analyst responsible for developing and executing a strategic plan to identify all legal risks, obligations, and areas of concern in the company's legal documents. You coordinate the analysis but delegate detailed investigation to specialized subagents.

AVAILABLE SUBAGENTS:
1. Analysis Subagent (unlimited use):
   - Use for deep investigation of specific document types or legal issues
   - Examples: "Analyze all employment agreements for restrictive covenants"
              "Review intellectual property assignments across all contracts"
   - This subagent has access to document analysis tools and web research
   - Each invocation works in isolation and returns a summary of findings

2. Create Report Subagent (ONE TIME USE ONLY):
   - Use ONLY when all analysis is complete
   - This subagent synthesizes all findings into a final report
   - Once called, you cannot call it again - ensure analysis is thorough first

YOUR WORKFLOW:
1. First, use write_todos to create a comprehensive analysis plan based on the document summaries provided
2. Break down the analysis into logical investigations (e.g., by document type, by legal issue)
3. Delegate each investigation to the Analysis subagent using the task() tool
4. As findings come back, review them and adjust your plan if needed
5. Keep notes in the filesystem about patterns, risks, and areas needing attention
6. Only when ALL investigations are complete, call the Create Report subagent ONCE

PLANNING CONSIDERATIONS:
- Consider document types: employment agreements, vendor contracts, IP licenses, etc.
- Consider legal issues: obligations, termination clauses, liability, IP rights, compliance
- Consider cross-cutting risks that appear across multiple documents
- Think about what legal research might be needed (case law, regulations, standards)

DELEGATION STRATEGY:
- Make each Analysis subagent task focused and specific
- Provide clear objectives: what to look for, what questions to answer
- Don't overlap investigations - each should cover distinct ground
- Wait for results before delegating the next task if they're sequential

FILESYSTEM USAGE:
- Use /analysis/ for findings from each investigation
- Use /notes/ for your coordination notes and risk summaries
- The filesystem persists across your entire analysis session
- The Report subagent will read all files you create

CRITICAL RULES:
- Do NOT try to read documents directly - always use Analysis subagent
- Do NOT create the report yourself - always use Create Report subagent
- Do NOT call Create Report subagent until all investigations are complete
- DO maintain a clear plan and track progress systematically

Remember: You are the strategist and coordinator. Your job is to ensure nothing is missed and all findings are properly synthesized, not to do the detailed work yourself."""


def create_legal_risk_agent(
    anthropic_api_key: str = None,
    mcp_server_path: str = "./legal_doc_mcp_server.py",
    checkpointer = None,
    store = None
):
    """
    Create the main Legal Risk Analysis agent.
    
    This agent coordinates the entire analysis process, delegating detailed
    work to subagents while maintaining strategic oversight.
    
    Args:
        anthropic_api_key: API key for Claude (defaults to env var)
        mcp_server_path: Path to the MCP server script
        checkpointer: LangGraph checkpointer for state persistence
        store: LangGraph store for cross-thread memory
    
    Returns:
        Configured Deep Agent ready to conduct legal analysis
    """
    
    # Use environment variable if API key not provided
    if anthropic_api_key is None:
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")
    
    # Create checkpointer if not provided
    # This is required for human-in-the-loop functionality
    if checkpointer is None:
        checkpointer = MemorySaver()
    
    # Create store if not provided
    # This enables persistent memory across analysis sessions
    if store is None:
        store = InMemoryStore()
    
    # Import subagent creators
    from .analysis_subagent import create_analysis_subagent
    from .report_subagent import create_report_subagent
    
    # Configure the filesystem backend
    # We use a CompositeBackend to route /memories/ to persistent storage
    # while keeping working files ephemeral
    def create_backend(runtime):
        return CompositeBackend(
            default=StateBackend(runtime),  # Ephemeral working files
            routes={
                "/memories/": StoreBackend(runtime)  # Persistent memories
            }
        )
    
    # Define the Analysis subagent configuration
    # This subagent can be called unlimited times for different investigations
    analysis_subagent_config = {
        "name": "Analysis",
        "description": """Use this subagent for detailed investigation of specific legal issues or document types.
        
Examples of when to use:
- "Analyze all employment agreements for non-compete and confidentiality clauses"
- "Review vendor contracts for liability and indemnification provisions"  
- "Examine intellectual property assignment clauses across all agreements"
- "Investigate termination conditions and notice requirements"

This subagent has access to document analysis tools and web research capabilities.
It will conduct a thorough investigation and return a summary of findings.""",
        
        "system_prompt": """You are a specialized legal analyst conducting detailed document investigation.

You have been assigned a specific legal analysis task. Your job is to:
1. Use list_documents to see what's available
2. Identify relevant documents based on your assignment
3. Use get_documents to access document content (this includes page summaries and legally significant pages)
4. Use get_page_text for additional pages if needed
5. Use get_page_image sparingly - only when visual layout is critical
6. Use web_search to research legal standards, precedents, or regulations
7. Document your findings clearly in files

IMPORTANT GUIDELINES:
- Be thorough but focused on your assigned task
- Look for risks, obligations, deadlines, and problematic clauses
- Compare provisions across documents to identify patterns
- Research legal standards when you find questionable provisions
- Document specific page numbers and quote key language
- Write your findings in clear, organized files

Your findings will be used by the main agent to create the final report.""",
        
        "tools": [],  # We'll add MCP tools dynamically
        "model": "claude-sonnet-4-5-20250929",
    }
    
    # Define the Create Report subagent configuration
    # This subagent can only be called ONCE - use it wisely
    report_subagent_config = {
        "name": "CreateReport",
        "description": """Use this subagent ONCE when all analysis is complete to generate the final report.

This subagent will:
- Read all analysis findings from the filesystem
- Synthesize findings into a comprehensive report
- Structure the report with executive summary, detailed findings, and recommendations
- Format the report professionally for executive review

WARNING: This can only be used ONE TIME. Do not call this until you have completed all investigations and are certain you have comprehensive findings.""",
        
        "system_prompt": """You are a legal report writer creating a comprehensive Legal Risk Analysis Report.

Your task is to synthesize all analysis findings into a polished, professional report suitable for executive review.

AVAILABLE INFORMATION:
- All analysis findings are stored in the filesystem under /analysis/
- Coordination notes from the main agent may be in /notes/
- Read all files to understand the complete picture

REPORT STRUCTURE:
1. Executive Summary (2-3 paragraphs)
   - High-level overview of documents analyzed
   - Key risks and concerns identified
   - Critical action items

2. Risk Categories (organize by type)
   - Contractual Obligations and Deadlines
   - Liability and Indemnification Concerns  
   - Intellectual Property Issues
   - Regulatory Compliance Risks
   - Termination and Dispute Resolution
   - Other Material Concerns
   
   For each risk:
   - Description of the issue
   - Specific documents/pages affected
   - Severity assessment (High/Medium/Low)
   - Potential impact
   - Recommended action

3. Document-Specific Findings
   - Summary for each major document reviewed
   - Key provisions and concerns
   - Cross-references to risk categories

4. Recommendations
   - Priority actions required
   - Areas needing further legal review
   - Policy or process improvements

FORMATTING:
- Use clear headers and sections
- Use bullet points for readability
- Include specific page references
- Use professional, clear language
- Be concise but comprehensive

Write the complete report to /report/legal_risk_analysis_report.md""",
        
        "model": "claude-sonnet-4-5-20250929",
        "middleware": []  # Only needs filesystem access
    }
    
    # Configure human-in-the-loop interrupts
    # These tools will pause execution for human approval
    interrupt_config = {
        "write_todos": True,  # Approve the analysis plan
        "task": True,  # Approve subagent delegations
        "write_file": True,  # Review files being created
        "edit_file": True,  # Review file modifications
    }
    
    # Create the main agent
    # This brings together all the components we've configured
    agent = create_deep_agent(
        model="claude-sonnet-4-5-20250929",
        system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
        backend=create_backend,
        checkpointer=checkpointer,
        store=store,
        subagents=[analysis_subagent_config, report_subagent_config],
        interrupt_on=interrupt_config
    )
    
    return agent


def format_document_summaries_for_prompt(db):
    """
    Format all document summaries for inclusion in the initial prompt.
    
    This gives the main agent a complete overview of available documents
    so it can formulate an effective analysis strategy.
    """
    from database import LegalDocumentDatabase
    
    if isinstance(db, str):
        db = LegalDocumentDatabase(db)
    
    documents = db.get_all_documents()
    
    if not documents:
        return "No documents found in the data room."
    
    summary_lines = [
        "=== LEGAL DOCUMENTS DATA ROOM ===",
        f"\nTotal Documents: {len(documents)}\n",
        "Document Summaries:\n"
    ]
    
    for doc in documents:
        summary_lines.extend([
            f"Document {doc['doc_id']}: {doc['filename']}",
            f"  Summary: {doc['summdesc']}",
            f"  Pages: {doc['total_pages']} total, {doc['legally_significant_pages']} legally significant",
            ""
        ])
    
    return "\n".join(summary_lines)
