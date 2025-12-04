# agents/__init__.py
"""
Legal Risk Analysis Deep Agent System

This module implements a hierarchical agent system for analyzing legal documents.
The system consists of:
- Main agent: Strategic coordinator and planner
- Analysis subagent: Deep document investigation and research
- Report subagent: Synthesis and report generation
"""

from .main_agent import create_legal_risk_agent
from .analysis_subagent import create_analysis_subagent
from .report_subagent import create_report_subagent

__all__ = [
    'create_legal_risk_agent',
    'create_analysis_subagent', 
    'create_report_subagent'
]
