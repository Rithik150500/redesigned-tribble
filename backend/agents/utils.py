# agents/utils.py
"""
Utility functions for the agent system.
"""

from database import LegalDocumentDatabase


def format_document_summaries_for_prompt(db: LegalDocumentDatabase) -> str:
    """
    Format document summaries for inclusion in the agent's initial prompt.

    This provides the main agent with a high-level view of all available
    documents so it can plan an effective analysis strategy.

    Args:
        db: Database connection

    Returns:
        Formatted string with document summaries
    """
    documents = db.get_all_documents()

    if not documents:
        return "No documents are currently available in the data room."

    lines = [
        "=== AVAILABLE DOCUMENTS IN DATA ROOM ===\n",
        f"Total Documents: {len(documents)}\n"
    ]

    for doc in documents:
        lines.append(
            f"\nDocument ID: {doc['doc_id']}\n"
            f"Filename: {doc['filename']}\n"
            f"Summary: {doc['summdesc'] or 'No summary available'}\n"
            f"Pages: {doc['total_pages']} total, {doc['legally_significant_pages']} legally significant\n"
        )

    lines.append(
        "\nUse the Analysis subagent to investigate specific documents or legal issues."
    )

    return "\n".join(lines)


def extract_action_results_from_interrupt(interrupt_data: dict) -> list:
    """
    Extract action results from interrupt data for processing.

    Args:
        interrupt_data: Interrupt data from agent execution

    Returns:
        List of action result dictionaries
    """
    if not interrupt_data:
        return []

    action_requests = interrupt_data.get("action_requests", [])
    return [
        {
            "action_id": action.get("id"),
            "tool_name": action.get("name"),
            "arguments": action.get("args", {}),
            "metadata": action.get("metadata", {})
        }
        for action in action_requests
    ]


def build_filesystem_summary(filesystem_dict: dict, max_depth: int = 3) -> str:
    """
    Build a human-readable summary of the agent's filesystem.

    Args:
        filesystem_dict: Dictionary representing filesystem structure
        max_depth: Maximum depth to traverse

    Returns:
        Formatted string showing directory tree
    """
    def walk_dir(d: dict, depth: int = 0, prefix: str = "") -> list:
        if depth > max_depth:
            return []

        lines = []
        items = list(d.items())

        for i, (name, value) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "

            if isinstance(value, dict):
                # Directory
                lines.append(f"{prefix}{connector}{name}/")
                extension = "    " if is_last else "│   "
                lines.extend(walk_dir(value, depth + 1, prefix + extension))
            else:
                # File
                lines.append(f"{prefix}{connector}{name}")

        return lines

    if not filesystem_dict:
        return "(empty filesystem)"

    tree_lines = walk_dir(filesystem_dict)
    return "\n".join(tree_lines)
