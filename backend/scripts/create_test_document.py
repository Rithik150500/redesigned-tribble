#!/usr/bin/env python3
"""
Create a simple test PDF document for demonstrating the system.

This script creates a minimal PDF with sample legal content to help
users test the system without needing real legal documents.
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from pathlib import Path


def create_test_document(output_path: Path):
    """
    Create a sample legal document PDF for testing.

    This creates a mock employment agreement with various clauses
    that the system can analyze.
    """

    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for PDF elements
    story = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#000000',
        spaceAfter=30,
        alignment=1  # Center
    )
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    # Title
    story.append(Paragraph("EMPLOYMENT AGREEMENT", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Introduction
    story.append(Paragraph(
        "This Employment Agreement (the 'Agreement') is entered into as of January 1, 2024, "
        "by and between TechCorp Inc., a Delaware corporation (the 'Company'), and "
        "Jane Smith (the 'Employee').",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Section 1: Position and Duties
    story.append(Paragraph("1. POSITION AND DUTIES", heading_style))
    story.append(Paragraph(
        "The Company hereby employs Employee as Senior Software Engineer. Employee shall "
        "perform such duties and responsibilities as are customarily associated with such "
        "position and such other duties as may be assigned by the Company's Chief Technology Officer.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Section 2: Compensation
    story.append(Paragraph("2. COMPENSATION AND BENEFITS", heading_style))
    story.append(Paragraph(
        "The Company shall pay Employee a base salary of $150,000 per annum, payable in "
        "accordance with the Company's standard payroll practices. Employee shall be eligible "
        "for annual bonuses at the discretion of the Company's Board of Directors.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Page break for more content
    story.append(PageBreak())

    # Section 3: Confidentiality
    story.append(Paragraph("3. CONFIDENTIALITY", heading_style))
    story.append(Paragraph(
        "Employee acknowledges that during employment, Employee will have access to and "
        "become acquainted with confidential information concerning the Company's business, "
        "including but not limited to: trade secrets, customer lists, product development plans, "
        "source code, business strategies, and financial information. Employee agrees to hold "
        "all such information in strict confidence and not to disclose such information to any "
        "third party without prior written consent of the Company.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Section 4: Intellectual Property
    story.append(Paragraph("4. INTELLECTUAL PROPERTY ASSIGNMENT", heading_style))
    story.append(Paragraph(
        "Employee agrees that all inventions, discoveries, improvements, and innovations "
        "(collectively 'Inventions') conceived, developed, or reduced to practice by Employee "
        "during employment, whether during business hours or not, that relate to the Company's "
        "actual or anticipated business shall be the sole and exclusive property of the Company. "
        "Employee hereby assigns to the Company all rights, title, and interest in such Inventions.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Section 5: Non-Compete
    story.append(Paragraph("5. NON-COMPETITION AND NON-SOLICITATION", heading_style))
    story.append(Paragraph(
        "During employment and for a period of twelve (12) months following termination, "
        "Employee shall not, directly or indirectly: (a) engage in any business that competes "
        "with the Company's business within a 50-mile radius of any Company office; (b) solicit "
        "or attempt to solicit any employee, contractor, or consultant of the Company to leave "
        "their employment or engagement with the Company; or (c) solicit any customer or client "
        "of the Company for any purpose that competes with the Company's business.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Page break
    story.append(PageBreak())

    # Section 6: Termination
    story.append(Paragraph("6. TERMINATION", heading_style))
    story.append(Paragraph(
        "Either party may terminate this Agreement at any time, with or without cause, upon "
        "thirty (30) days' written notice to the other party. Upon termination, Employee shall "
        "return all Company property and confidential information. The confidentiality, "
        "intellectual property, and non-competition provisions shall survive termination.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Section 7: Indemnification
    story.append(Paragraph("7. INDEMNIFICATION", heading_style))
    story.append(Paragraph(
        "Company shall indemnify and hold harmless Employee from and against any claims, "
        "damages, or liabilities arising out of Employee's performance of duties under this "
        "Agreement, except in cases of gross negligence or willful misconduct by Employee.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Section 8: Governing Law
    story.append(Paragraph("8. GOVERNING LAW AND DISPUTE RESOLUTION", heading_style))
    story.append(Paragraph(
        "This Agreement shall be governed by and construed in accordance with the laws of "
        "the State of Delaware, without regard to its conflict of laws principles. Any disputes "
        "arising under this Agreement shall be resolved through binding arbitration in accordance "
        "with the rules of the American Arbitration Association.",
        normal_style
    ))
    story.append(Spacer(1, 0.2*inch))

    # Signatures
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("IN WITNESS WHEREOF, the parties have executed this Agreement.", normal_style))
    story.append(Spacer(1, 0.5*inch))

    story.append(Paragraph("_" * 50, normal_style))
    story.append(Paragraph("TechCorp Inc.", normal_style))
    story.append(Paragraph("By: John Doe, CEO", normal_style))
    story.append(Paragraph("Date: January 1, 2024", normal_style))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("_" * 50, normal_style))
    story.append(Paragraph("Employee: Jane Smith", normal_style))
    story.append(Paragraph("Date: January 1, 2024", normal_style))

    # Build PDF
    doc.build(story)
    print(f"✓ Created test document: {output_path}")


if __name__ == "__main__":
    # Create the test document in the data/documents directory
    output_dir = Path(__file__).parent.parent / "data" / "documents"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "sample_employment_agreement.pdf"

    try:
        create_test_document(output_file)
        print(f"\nTest document created successfully!")
        print(f"Location: {output_file}")
        print(f"\nNext step: Run 'python scripts/ingest_documents.py' to process it.")
    except ImportError:
        print("Error: reportlab not installed.")
        print("Install it with: pip install reportlab")
    except Exception as e:
        print(f"Error creating test document: {e}")
