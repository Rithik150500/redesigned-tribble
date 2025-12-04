# agents/report_subagent.py
"""
Report Creation Subagent

This subagent synthesizes all analysis findings into a comprehensive
legal risk analysis report.
"""

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
import os

# System prompt for Report subagent
REPORT_SUBAGENT_PROMPT = """You are a legal report writer creating a comprehensive Legal Risk Analysis Report.

Your task is to synthesize all analysis findings into a polished, professional report suitable for executive review.

AVAILABLE INFORMATION:
All analysis findings from the investigation phase are stored in the filesystem.
Read all files to understand the complete picture of legal risks identified.

REPORT STRUCTURE:

# LEGAL RISK ANALYSIS REPORT

## Executive Summary

Provide a 2-3 paragraph overview:
- What documents were analyzed
- Key risks and concerns identified  
- Critical action items requiring immediate attention

## Risk Assessment by Category

Organize findings into logical categories (adjust based on actual findings):

### Contractual Obligations and Deadlines
- List key obligations
- Note critical deadlines
- Assess compliance status

### Liability and Indemnification
- Identify liability exposure
- Review indemnification clauses
- Note limitations or concerns

### Intellectual Property
- Review IP assignment provisions
- Check ownership clarity
- Identify protection gaps

### Regulatory Compliance
- Note compliance requirements
- Identify gaps or concerns
- Assess risk level

### Termination and Dispute Resolution
- Review termination conditions
- Note dispute mechanisms
- Identify procedural requirements

### Other Material Concerns
- Any other significant findings

For each risk identified:
- Description: Clear explanation of the issue
- Location: Specific documents and page numbers
- Severity: High / Medium / Low
- Impact: Potential consequences
- Recommendation: Suggested action

## Document-Specific Findings

Provide a summary for each major document analyzed:
- Document name and type
- Key provisions
- Main concerns
- Cross-references to risk categories above

## Recommendations and Next Steps

Priority 1 (Immediate Action Required):
- List critical items needing immediate attention

Priority 2 (Near-term Review):
- Items needing attention within 30-90 days

Priority 3 (Ongoing Monitoring):
- Items to track or review periodically

Additional Recommendations:
- Process improvements
- Policy updates
- Areas needing specialized legal counsel

## Appendix

- Methodology: How the analysis was conducted
- Documents analyzed: Complete list with page counts
- Limitations: Any gaps in analysis or areas not covered

---

FORMATTING GUIDELINES:
- Use markdown formatting for clarity
- Use headers and subheaders appropriately
- Use bullet points for readability
- Include specific page references for all findings
- Use professional, clear language
- Be concise but comprehensive
- Prioritize findings by severity

Write the complete report to /report/legal_risk_analysis_report.md

Remember: This report will be read by executives and legal counsel.
It must be thorough, accurate, well-organized, and actionable."""


def create_report_subagent(
    anthropic_api_key: str = None
):
    """
    Create a Report Creation subagent for synthesizing findings.
    
    This subagent only needs filesystem access - it reads all the analysis
    files and creates the final report.
    
    Args:
        anthropic_api_key: API key for Claude
    
    Returns:
        Configured Report subagent
    """
    
    if anthropic_api_key is None:
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    agent = create_deep_agent(
        model="claude-sonnet-4-5-20250929",
        system_prompt=REPORT_SUBAGENT_PROMPT,
        backend=lambda rt: StateBackend(rt),  # Just needs filesystem
        # No additional tools needed - just filesystem access
    )
    
    return agent
