import re
import io
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from app.schemas import RepoAnalysisResponse

class NumberedCanvas(canvas.Canvas):
    """
    Canvas to handle professional two-pass page numbering and Neura AI Indigo/Cyan cover layouts.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Draw Neura AI dark blue/charcoal background for the cover page
            self.saveState()
            self.setFillColor(colors.HexColor("#090D16")) # Charcoal Base
            self.rect(0, 0, 612, 792, fill=True, stroke=False)
            
            # Bottom dual-accent bars (Indigo + Cyan)
            self.setFillColor(colors.HexColor("#6366F1")) # Indigo
            self.rect(0, 4, 612, 8, fill=True, stroke=False)
            self.setFillColor(colors.HexColor("#06B6D4")) # Cyan
            self.rect(0, 0, 612, 4, fill=True, stroke=False)
            
            # Top dual-accent bars (Indigo + Cyan)
            self.setFillColor(colors.HexColor("#6366F1")) # Indigo
            self.rect(0, 780, 612, 8, fill=True, stroke=False)
            self.setFillColor(colors.HexColor("#06B6D4")) # Cyan
            self.rect(0, 776, 612, 4, fill=True, stroke=False)
            self.restoreState()
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (Clean minimalist running header)
        self.drawString(54, 755, "DEVPILOT AI REPOSITORY REPORT")
        self.setFont("Helvetica", 8)
        self.drawRightString(558, 755, "TECHNICAL DUE DILIGENCE AUDIT")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 747, 558, 747)
        
        # Indigo + Cyan tick mark on the header line
        self.setFillColor(colors.HexColor("#6366F1")) # Indigo
        self.rect(54, 745.5, 24, 3, fill=True, stroke=False)
        self.setFillColor(colors.HexColor("#06B6D4")) # Cyan
        self.rect(78, 745.5, 16, 3, fill=True, stroke=False)
        
        # Footer
        self.line(54, 58, 558, 58)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(54, 42, "Confidential — Generated with DevPilot AI")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 42, page_text)
        self.restoreState()


class PDFGenerator:
    @staticmethod
    def _clean_markdown_to_xml(text: str) -> str:
        """
        Converts basic markdown tags from AI summary into ReportLab paragraph XML tags.
        """
        if not text:
            return ""
            
        # Clean special XML entities
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Restore valid tags we will inject
        def repl_amp(t):
            return t.replace("&amp;lt;", "<").replace("&amp;gt;", ">")

        # Headers
        text = re.sub(r"###\s+(.*)", r"&lt;font size=11 color='#6366F1'&gt;&lt;b&gt;\1&lt;/b&gt;&lt;/font&gt;", text)
        text = re.sub(r"####\s+(.*)", r"&lt;font size=9.5 color='#06B6D4'&gt;&lt;b&gt;\1&lt;/b&gt;&lt;/font&gt;", text)
        
        # Bold text
        text = re.sub(r"\*\*(.*?)\*\*", r"&lt;b&gt;\1&lt;/b&gt;", text)
        
        # Bullet list items
        text = re.sub(r"^\s*[\-\*]\s+(.*)", r"&bull; \1", text, flags=re.MULTILINE)
        
        # Paragraph spacing - replace newlines with line breaks
        text = text.replace("\n", "<br/>")
        
        # Re-allow XML tag formats
        text = repl_amp(text)
        return text

    @staticmethod
    def _create_section_header(title_text: str, h1_style: ParagraphStyle) -> Table:
        """
        Creates a premium section header with a thick left-border indigo brand accent stripe.
        """
        p = Paragraph(title_text.upper(), h1_style)
        t = Table([[p]], colWidths=[504])
        t.setStyle(TableStyle([
            ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor("#6366F1")), # Electric Indigo left-border
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    @classmethod
    def generate(cls, analysis: RepoAnalysisResponse) -> bytes:
        """
        Compiles the entire analysis payload into a professional multi-page PDF.
        """
        buffer = io.BytesIO()
        
        # 54pt margin = 0.75 in. Top & bottom margins accommodate header/footer drawing
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=68,
            bottomMargin=68
        )
        
        styles = getSampleStyleSheet()
        
        # Define custom styles for Cover page (Dark background)
        cover_title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=colors.white,
            alignment=0, # Left-aligned
            spaceAfter=10
        )
        
        cover_subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#94A3B8"),
            spaceAfter=30
        )
        
        cover_meta_label = ParagraphStyle(
            "CoverMetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#94A3B8")
        )
        
        cover_meta_val = ParagraphStyle(
            "CoverMetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.white
        )

        # Body page styles (Light background)
        h1_style = ParagraphStyle(
            "SectionH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#111A24"),
            spaceBefore=0,
            spaceAfter=0,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8
        )
 
        story = []

        # =========================================================================
        # 1. COVER PAGE
        # =========================================================================
        story.append(Spacer(1, 90))
        story.append(Paragraph("DEVPILOT AI DUE DILIGENCE AUDIT", cover_title_style))
        story.append(Paragraph("Investor-Grade Codebase Health, Security Scan, and Technical Maturity Report", cover_subtitle_style))
        story.append(Spacer(1, 15))
        
        # Repository Metadata Box
        meta_data = [
            [Paragraph("Target Repository", cover_meta_label), Paragraph(f"{analysis.metadata.owner}/{analysis.metadata.name}", cover_meta_val)],
            [Paragraph("Repository URL", cover_meta_label), Paragraph(analysis.repo_url, cover_meta_val)],
            [Paragraph("Audit Timestamp", cover_meta_label), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"), cover_meta_val)],
            [Paragraph("Primary Languages", cover_meta_label), Paragraph(", ".join(list(analysis.metadata.languages.keys())[:3]), cover_meta_val)],
            [Paragraph("License Type", cover_meta_label), Paragraph(analysis.metadata.license or "Not Declared", cover_meta_val)],
        ]
        
        meta_table = Table(meta_data, colWidths=[140, 364])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#111A24")), # Deep charcoal card
            ('PADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor("#223142")),
            ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor("#6366F1")), # Indigo accent left border
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#223142")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 35))

        # Overall Score Circle/Badge flowable
        score_val = analysis.scores.overall
        if score_val >= 80:
            score_color = "#06B6D4" # Neon Cyan for passed score
            rating_text = "PASSED - EXCELLENT HYGIENE"
        elif score_val >= 60:
            score_color = "#D97706" # Amber
            rating_text = "PASSED WITH RESERVATIONS"
        else:
            score_color = "#E11D48" # Rose
            rating_text = "FAILED - HIGH-RISK / ARCHITECTURAL DEBT"

        score_text_style = ParagraphStyle(
            "ScoreText",
            fontName="Helvetica-Bold",
            fontSize=64,
            leading=64,
            textColor=colors.HexColor(score_color),
            alignment=1
        )
        
        rating_label_style = ParagraphStyle(
            "RatingLabel",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor(score_color),
            alignment=1
        )

        score_box_data = [
            [Paragraph(f"{score_val}", score_text_style)],
            [Paragraph("OVERALL INTELLIGENCE SCORE", ParagraphStyle("ScoreLbl", fontName="Helvetica-Bold", fontSize=10, leading=12, alignment=1, textColor=colors.HexColor("#94A3B8")))],
            [Paragraph(rating_text, rating_label_style)]
        ]
        score_table = Table(score_box_data, colWidths=[200])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#111A24")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 16),
            ('LINELEFT', (0, 0), (0, -1), 4, colors.HexColor(score_color)),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#223142")),
        ]))
        
        # Center the score block on cover
        wrapper_table = Table([[score_table]], colWidths=[504])
        wrapper_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(wrapper_table)
        story.append(PageBreak())

        # =========================================================================
        # 2. EXECUTIVE SUMMARY
        # =========================================================================
        story.append(cls._create_section_header("EXECUTIVE SECURITY & ARCHITECTURE ASSESSMENT", h1_style))
        story.append(Spacer(1, 15))
        
        ai_paragraph_style = ParagraphStyle(
            "AIParagraph",
            parent=body_style,
            fontSize=9.5,
            leading=15,
            spaceAfter=10
        )
        
        assessment_paragraphs = analysis.ai_assessment.split("\n\n")
        for para in assessment_paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if para.startswith("###"):
                clean_text = para.replace("###", "").strip()
                sub_style = ParagraphStyle(
                    "AISubH2",
                    parent=styles["Heading2"],
                    fontName="Helvetica-Bold",
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor("#6366F1"), # Electric Indigo Accent
                    spaceBefore=12,
                    spaceAfter=6,
                    keepWithNext=True
                )
                story.append(Paragraph(clean_text, sub_style))
            elif para.startswith("####"):
                clean_text = para.replace("####", "").strip()
                sub_style = ParagraphStyle(
                    "AISubH3",
                    parent=styles["Heading3"],
                    fontName="Helvetica-Bold",
                    fontSize=10,
                    leading=13,
                    textColor=colors.HexColor("#06B6D4"), # Neon Cyan
                    spaceBefore=10,
                    spaceAfter=4,
                    keepWithNext=True
                )
                story.append(Paragraph(clean_text, sub_style))
            else:
                clean_text = cls._clean_markdown_to_xml(para)
                story.append(Paragraph(clean_text, ai_paragraph_style))
                story.append(Spacer(1, 6))

        story.append(PageBreak())

        # =========================================================================
        # 3. SCORE BREAKDOWNS & METRICS
        # =========================================================================
        story.append(cls._create_section_header("DETAILED CATEGORY AUDITS", h1_style))
        story.append(Spacer(1, 15))
        
        # Category breakdown table
        cat_header_style = ParagraphStyle("CatH", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white)
        cat_body_bold = ParagraphStyle("CatB", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#111A24"))
        
        breakdown_data = [
            [Paragraph("Category", cat_header_style), Paragraph("Scoring Weight", cat_header_style), Paragraph("Audit Grade", cat_header_style)],
            [Paragraph("Security & Compliance Scan", cat_body_bold), Paragraph("30%", body_style), Paragraph(f"{analysis.scores.security} / 100", cat_body_bold)],
            [Paragraph("Documentation & Setup Quality", cat_body_bold), Paragraph("30%", body_style), Paragraph(f"{analysis.scores.documentation} / 100", cat_body_bold)],
            [Paragraph("Commit Frequency & Git History", cat_body_bold), Paragraph("20%", body_style), Paragraph(f"{analysis.scores.commits} / 100", cat_body_bold)],
            [Paragraph("Project Structure & Hygiene", cat_body_bold), Paragraph("20%", body_style), Paragraph(f"{analysis.scores.structure} / 100", cat_body_bold)],
        ]
        
        breakdown_table = Table(breakdown_data, colWidths=[200, 150, 154])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#111A24")),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(breakdown_table)
        story.append(Spacer(1, 25))

        # Security scan section
        story.append(Paragraph("SECURITY SCAN DETAILS", ParagraphStyle("H2", parent=h1_style, fontSize=11, leading=14, textColor=colors.HexColor("#6366F1"))))
        story.append(Spacer(1, 10))
        
        # Hardcoded Secrets Table
        if analysis.security.secrets:
            sec_lbl_style = ParagraphStyle("SecL", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#991B1B"))
            sec_body_style = ParagraphStyle("SecB", fontName="Helvetica", fontSize=8, leading=10)
            secrets_headers = [Paragraph("File Path", cat_header_style), Paragraph("Line", cat_header_style), Paragraph("Type", cat_header_style), Paragraph("Exposed Pattern Code snippet", cat_header_style)]
            secrets_rows = [secrets_headers]
            for s in analysis.security.secrets:
                secrets_rows.append([
                    Paragraph(s.file_path, sec_body_style),
                    Paragraph(str(s.line), sec_body_style),
                    Paragraph(s.secret_type, sec_lbl_style),
                    Paragraph(s.snippet, sec_body_style)
                ])
            secrets_table = Table(secrets_rows, colWidths=[130, 30, 80, 264])
            secrets_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7F1D1D")),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#FEE2E2")),
            ]))
            story.append(Paragraph("<b>Exposed Code Credentials:</b>", ParagraphStyle("SubSec", parent=body_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#991B1B"))))
            story.append(Spacer(1, 5))
            story.append(secrets_table)
            story.append(Spacer(1, 15))
        else:
            story.append(Paragraph("✓ <b>Hardcoded Secrets:</b> No credentials or API keys were detected in the source code.", ParagraphStyle("SecSafe", parent=body_style, textColor=colors.HexColor("#06B6D4"))))
            story.append(Spacer(1, 15))

        # Dependency CVE Table
        if analysis.security.vulnerabilities:
            vuln_lbl_high = ParagraphStyle("Vlh", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#991B1B"))
            vuln_lbl_med = ParagraphStyle("Vlm", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#D97706"))
            vuln_body_style = ParagraphStyle("Vlb", fontName="Helvetica", fontSize=8, leading=10)
            vuln_headers = [Paragraph("Package", cat_header_style), Paragraph("Current", cat_header_style), Paragraph("Severity", cat_header_style), Paragraph("CVE Summary Description", cat_header_style), Paragraph("Patched In", cat_header_style)]
            vuln_rows = [vuln_headers]
            for v in analysis.security.vulnerabilities:
                sev_style = vuln_lbl_high if v.severity.upper() in ["HIGH", "CRITICAL"] else vuln_lbl_med
                vuln_rows.append([
                    Paragraph(v.package_name, vuln_body_style),
                    Paragraph(v.current_version, vuln_body_style),
                    Paragraph(v.severity, sev_style),
                    Paragraph(v.description, vuln_body_style),
                    Paragraph(v.patched_version or "N/A", vuln_body_style)
                ])
            vuln_table = Table(vuln_rows, colWidths=[90, 50, 60, 234, 70])
            vuln_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#111A24")),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            story.append(Paragraph("<b>Package Dependency Vulnerabilities (OSV Database):</b>", ParagraphStyle("SubSec", parent=body_style, fontName="Helvetica-Bold")))
            story.append(Spacer(1, 5))
            story.append(vuln_table)
        else:
            story.append(Paragraph("✓ <b>Dependency Vulnerabilities:</b> No package CVEs found in repository configurations.", ParagraphStyle("SecSafe", parent=body_style, textColor=colors.HexColor("#06B6D4"))))

        story.append(PageBreak())

        # =========================================================================
        # 4. FIX-IT ROADMAP
        # =========================================================================
        story.append(cls._create_section_header("FIX-IT ROADMAP (RANKED BY IMPACT)", h1_style))
        story.append(Spacer(1, 15))
        story.append(Paragraph(
            "The following items represent quality improvements that directly increase the codebase's Overall Intelligence Score. "
            "Resolving these gaps is recommended for technical stability and auditing readiness.",
            body_style
        ))
        story.append(Spacer(1, 10))

        if analysis.roadmap:
            rm_h_style = ParagraphStyle("RmH", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)
            rm_body_style = ParagraphStyle("RmB", fontName="Helvetica", fontSize=8, leading=10)
            rm_body_bold = ParagraphStyle("RmBb", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#111A24"))
            
            rm_headers = [
                Paragraph("ID", rm_h_style),
                Paragraph("Issue Category", rm_h_style),
                Paragraph("Severity", rm_h_style),
                Paragraph("Score Gain", rm_h_style),
                Paragraph("Actionable Remedy", rm_h_style)
            ]
            rm_rows = [rm_headers]
            
            for rm in analysis.roadmap:
                sev_color = "#991B1B" if rm.severity == "High" else ("#D97706" if rm.severity == "Medium" else "#475569")
                sev_cell_style = ParagraphStyle("RmSev", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor(sev_color))
                
                # Combine suggested fix detail in table row
                fix_detail = f"<b>{rm.title}</b><br/>{rm.suggested_fix}"
                
                rm_rows.append([
                    Paragraph(rm.id, rm_body_bold),
                    Paragraph(rm.category, rm_body_style),
                    Paragraph(rm.severity, sev_cell_style),
                    Paragraph(f"+{rm.estimated_score_gain} pts", rm_body_bold),
                    Paragraph(fix_detail, rm_body_style)
                ])
                
            rm_table = Table(rm_rows, colWidths=[40, 80, 50, 60, 274])
            rm_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#111A24")),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            story.append(rm_table)
        else:
            story.append(Paragraph("✓ No improvements are required. The codebase meets all checked hygiene and security metrics.", ParagraphStyle("CleanRoad", parent=body_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#06B6D4"))))

        # Build PDF document
        doc.build(story, canvasmaker=NumberedCanvas)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
