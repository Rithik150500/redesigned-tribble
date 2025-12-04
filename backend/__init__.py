# backend/__init__.py
"""
Legal Risk Analysis System - Backend

A comprehensive system for AI-powered legal document analysis with
human-in-the-loop oversight.
"""

__version__ = "1.0.0"
__author__ = "Legal Risk Analysis Team"

from .database import LegalDocumentDatabase
from .document_processor import DocumentProcessor
from .agents import create_legal_risk_agent

__all__ = [
    "LegalDocumentDatabase",
    "DocumentProcessor",
    "create_legal_risk_agent",
]
