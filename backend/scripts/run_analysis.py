# run_analysis.py
"""
Command-line interface for running legal risk analysis.

This script demonstrates how to run the Deep Agent system with human-in-the-loop
approvals via command line. In production, this would be replaced with a web UI.
"""

import uuid
from pathlib import Path
import sys
import anthropic
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Import our agent system
from agents.main_agent import create_legal_risk_agent, format_document_summaries_for_prompt
from database import LegalDocumentDatabase


def print_separator(char="=", length=70):
    """Print a visual separator for clarity."""
    print("\n" + char * length)


def print_agent_message(message):
    """Pretty-print an agent message."""
    print_separator()
    print("AGENT:")
    print_separator("-")
    if hasattr(message, 'content'):
        print(message.content)
    else:
        print(message)


def print_tool_call(tool_name, arguments):
    """Pretty-print a tool call."""
    print_separator()
    print(f"TOOL CALL: {tool_name}")
    print_separator("-")
    print("Arguments:")
    for key, value in arguments.items():
        print(f"  {key}: {value}")


def handle_approval(interrupt_data):
    """
    Handle a human-in-the-loop approval request.
    
    This function displays the pending action and prompts for user decision.
    In a web UI, this would be a visual approval dialog.
    
    Returns:
        List of decisions (approve/edit/reject) for each action request
    """
    print_separator("*")
    print("*** HUMAN APPROVAL REQUIRED ***")
    print_separator("*")
    
    # Extract interrupt information
    # The interrupt contains action_requests (what the agent wants to do)
    # and review_configs (what decisions are allowed)
    interrupts = interrupt_data[0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]
    
    # Create a lookup map from tool name to review config
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}
    
    decisions = []
    
    for action in action_requests:
        tool_name = action["name"]
        arguments = action["args"]
        review_config = config_map[tool_name]
        
        print(f"\nThe agent wants to call: {tool_name}")
        print(f"With arguments: {arguments}")
        print(f"Allowed decisions: {review_config['allowed_decisions']}")
        
        # Show context based on tool type
        if tool_name == "write_todos":
            print("\nProposed To-Do List:")
            print(arguments.get("todos", ""))
        
        elif tool_name == "task":
            print("\nProposed Subagent Task:")
            print(f"  Subagent: {arguments.get('name', 'unknown')}")
            print(f"  Task: {arguments.get('task', '')}")
        
        elif tool_name in ["write_file", "edit_file"]:
            file_path = arguments.get("file_path", "unknown")
            content = arguments.get("content", "")
            print(f"\nFile: {file_path}")
            print(f"Content (first 500 chars):\n{content[:500]}...")
        
        elif tool_name == "get_documents":
            print(f"\nDocument IDs requested: {arguments.get('doc_ids', [])}")
        
        elif tool_name == "get_page_text":
            print(f"\nDocument ID: {arguments.get('doc_id')}")
            print(f"Pages: {arguments.get('page_nums', [])}")
        
        # Get user decision
        while True:
            decision_type = input("\nYour decision (approve/edit/reject): ").strip().lower()
            
            if decision_type not in review_config['allowed_decisions']:
                print(f"Invalid choice. Allowed: {review_config['allowed_decisions']}")
                continue
            
            if decision_type == "approve":
                decisions.append({"type": "approve"})
                print("✓ Approved")
                break
            
            elif decision_type == "reject":
                decisions.append({"type": "reject"})
                print("✗ Rejected")
                break
            
            elif decision_type == "edit":
                print("\nEditing is complex in CLI. For now, approve or reject.")
                print("(In a web UI, you'd have a form to edit the parameters)")
                continue
    
    return decisions


def run_analysis(user_message: str, db_path: str = "legal_documents.db"):
    """
    Run a legal risk analysis with human-in-the-loop approvals.
    
    This demonstrates the complete workflow:
    1. Initialize the agent system
    2. Send initial message with document summaries
    3. Handle approvals as the agent works
    4. Continue until analysis is complete
    
    Args:
        user_message: The initial analysis request from the user
        db_path: Path to the document database
    """
    
    print_separator("=")
    print("LEGAL RISK ANALYSIS SYSTEM")
    print_separator("=")
    
    # Initialize database and load document summaries
    print("\nLoading document summaries...")
    db = LegalDocumentDatabase(db_path)
    doc_summaries = format_document_summaries_for_prompt(db)
    
    print(f"Found {len(db.get_all_documents())} documents in database")
    
    # Create checkpointer and store
    checkpointer = MemorySaver()
    store = InMemoryStore()
    
    # Create the agent
    print("\nInitializing agent system...")
    agent = create_legal_risk_agent(
        checkpointer=checkpointer,
        store=store
    )
    
    # Create a unique thread ID for this analysis session
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"Analysis session: {thread_id}")
    
    # Combine user message with document summaries
    initial_message = f"""{user_message}

{doc_summaries}

Please develop a comprehensive analysis plan based on these documents."""
    
    print("\nStarting analysis...")
    print_separator()
    
    # Main interaction loop
    result = agent.invoke({
        "messages": [{"role": "user", "content": initial_message}]
    }, config=config)
    
    # Handle interrupts and continue until complete
    while result.get("__interrupt__"):
        # Display the interrupt and get user decisions
        decisions = handle_approval(result["__interrupt__"])
        
        # Resume with the decisions
        print("\nResuming agent execution...")
        result = agent.invoke(
            Command(resume={"decisions": decisions}),
            config=config
        )
    
    # Analysis complete
    print_separator("=")
    print("ANALYSIS COMPLETE")
    print_separator("=")
    
    # Display final messages
    final_messages = result.get("messages", [])
    if final_messages:
        print("\nFinal Agent Message:")
        print_agent_message(final_messages[-1])
    
    # Check if report was created
    print("\nChecking for generated report...")
    # In a real system, we'd read from the filesystem backend
    # For now, just indicate where to find it
    print("Report should be available at: /report/legal_risk_analysis_report.md")
    print("(Access through the agent's filesystem)")
    
    return result


def main():
    """Main entry point for command-line analysis."""
    
    print("\nLegal Risk Analysis System - Command Line Interface")
    print("=" * 70)
    
    # Check database exists
    db_path = "legal_documents.db"
    if not Path(db_path).exists():
        print(f"\nError: Database '{db_path}' not found.")
        print("Please run ingest_documents.py first to process documents.")
        sys.exit(1)
    
    # Get analysis request from user
    print("\nWhat would you like to analyze?")
    print("Example: 'Conduct a comprehensive legal risk analysis focusing on")
    print("         contractual obligations, IP rights, and liability provisions'")
    print()
    
    user_message = input("Your request: ").strip()
    
    if not user_message:
        print("No request provided. Exiting.")
        sys.exit(1)
    
    # Run the analysis
    try:
        run_analysis(user_message, db_path)
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
