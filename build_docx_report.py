"""
BioHarvest-Sim: Automated DOCX Document Compiler (Human Math Notation Edition)
==============================================================================
Compiles CCP_INTERNATIONAL_PROJECT_REPORT.md into a high-standard
Microsoft Word (.docx) project report with:
- Font Family: Times New Roman
- Body Text Size: 12 pt, 1.15 line spacing, 6pt paragraph after
- Heading 1: 18 pt, Bold, Times New Roman, with subtle accent color
- Heading 2: 14 pt, Bold, Times New Roman
- Heading 3: 12.5 pt, Bold, Times New Roman
- Clean Human Mathematical Notation:
    * No raw LaTeX tags (\\frac, \\mathbf, \\text, etc.)
    * Real fractions with '/' and clean parentheses
    * Natural Greek letters (λ, ρ, σ, δ, ε, θ, α, μ)
    * Proper mathematical operators (·, ×, Σ, Π, ≥, ≤, ≠, ≈, →, ↔)
    * Clear subscripts and superscripts (λ₁, v₁, u₁, w₁, R₀, T_c, Lᵏ, P⁻¹)
- Professional Tables with shaded header and clean grid
- 1-inch standard margins
"""

import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn


def clean_math_text(text: str) -> str:
    """
    Transform raw LaTeX expressions into clean, natural, human-written math notation
    exactly as a mathematician or student writes on paper.
    """
    if not text:
        return ""

    # Remove LaTeX math delimiters $ and $$
    text = text.replace("$$", "").replace("$", "")

    # Recursively convert \frac{numerator}{denominator} into (numerator) / (denominator)
    while "\\frac" in text:
        text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1) / (\2)", text)

    # Remove formatting wrappers: \mathbf{...}, \text{...}, \mathit{...}, \mathrm{...}
    text = re.sub(r"\\(mathbf|text|mathit|mathrm)\{([^{}]+)\}", r"\2", text)

    # Common LaTeX symbol replacements to clean human mathematical characters
    replacements = [
        ("\\lambda_1", "λ₁"),
        ("\\lambda_2", "λ₂"),
        ("\\lambda_j", "λⱼ"),
        ("\\lambda", "λ"),
        ("\\rho(L)", "ρ(L)"),
        ("\\rho", "ρ"),
        ("\\alpha_i", "αᵢ"),
        ("\\alpha", "α"),
        ("\\sigma_f^2", "σ_f²"),
        ("\\sigma_s^2", "σ_s²"),
        ("\\sigma", "σ"),
        ("\\delta_{cat}", "δ_cat"),
        ("\\delta", "δ"),
        ("\\epsilon", "ε"),
        ("\\theta", "θ"),
        ("\\mu", "μ"),
        ("\\sum_{i=1}^n", "Σ (i=1 to n)"),
        ("\\sum", "Σ"),
        ("\\prod_{j=1}^{i-1}", "Π (j=1 to i-1)"),
        ("\\prod", "Π"),
        ("\\ge", "≥"),
        ("\\le", "≤"),
        ("\\ne", "≠"),
        ("\\times", "×"),
        ("\\cdot", "·"),
        ("\\approx", "≈"),
        ("\\to", "→"),
        ("\\in", "∈"),
        ("\\iff", "<=>"),
        ("\\implies", "=>"),
        ("\\forall", "for all"),
        ("\\partial", "∂"),
        ("\\dots", "..."),
        ("\\det", "det"),
        ("\\ln", "ln"),
        ("\\exp", "exp"),
        ("\\mathbb{R}^n_{\\ge 0}", "Rⁿ (non-negative)"),
        ("\\mathbb{R}^n_{> 0}", "Rⁿ (strictly positive)"),
        ("\\mathbb{R}^n", "Rⁿ"),
        ("\\mathbb{R}", "R"),
        ("\\mathbb{Z}^+", "Positive Integers"),
        ("\\mathbb{Z}", "Z"),
        ("\\mathbb{C}", "Complex Numbers"),
        ("\\left(", "("),
        ("\\right)", ")"),
        ("\\left[", "["),
        ("\\right]", "]"),
        ("\\left\\{", "{"),
        ("\\right\\}", "}"),
        ("\\left", ""),
        ("\\right", ""),
        ("\\quad", "  "),
        ("\\qquad", "    "),
        ("\\_", "_"),
        ("\\%", "%"),
        ("v_{1,i}", "v₁,ᵢ"),
        ("u_{1,i}", "u₁,ᵢ"),
        ("x_{i,k}", "xᵢ(k)"),
        ("x_{k+1}", "x(k+1)"),
        ("x_k", "x(k)"),
        ("x_0", "x(0)"),
        ("L^k", "Lᵏ"),
        ("D^k", "Dᵏ"),
        ("P^{-1}", "P⁻¹"),
        ("P^-1", "P⁻¹"),
        ("R_0", "R₀"),
        ("w_1", "w₁"),
        ("v_1", "v₁"),
        ("u_1", "u₁"),
        ("h^*", "h*"),
        ("x^*", "x*"),
        ("c^T", "cᵀ"),
        ("u^T", "uᵀ"),
        ("L^T", "Lᵀ"),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    # Clean any remaining rogue backslashes before known words
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)

    return text


def set_cell_background(cell, fill_hex="1E3A8A"):
    """Set background color of a table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    """Set inner cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


# ── Figure path map: figure caption keyword → PNG filename ───────────────────
_CCP_DIR = os.path.dirname(os.path.abspath(__file__))
_FIG_DIR = os.path.join(_CCP_DIR, 'figures')

FIGURE_MAP = {
    'Figure 1.1': 'fig_1_1_architecture.png',
    'Figure 2.1': 'fig_2_1_leslie_matrix.png',
    'Figure 2.2': 'fig_2_2_eigen_spectrum.png',
    'Figure 2.3': 'fig_2_3_yield_curve.png',
    'Figure 3.1': 'fig_3_1_module_diagram.png',
    'Figure 4.1': 'fig_4_1_trajectories.png',
    'Figure 4.2': 'fig_4_2_3d_surface.png',
    'Figure 4.3': 'fig_4_3_phase_portrait.png',
    'Figure 4.4': 'fig_4_4_monte_carlo.png',
}


def insert_figure(doc, fig_key: str, caption_text: str):
    """Embed a figure PNG into the document with a centered caption below it."""
    img_path = os.path.join(_FIG_DIR, FIGURE_MAP.get(fig_key, ''))
    if not os.path.isfile(img_path):
        return  # Skip silently if image not generated yet

    # Insert image centered
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_img.add_run()
    run.add_picture(img_path, width=Inches(6.0))
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after  = Pt(2)

    # Caption below image: italic, centered, smaller font
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = p_cap.add_run(caption_text)
    cap_run.font.name   = 'Times New Roman'
    cap_run.font.size   = Pt(10)
    cap_run.font.italic = True
    cap_run.font.bold   = False
    cap_run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after  = Pt(12)


def build_docx_report(md_path: str, docx_path: str):
    doc = Document()

    # Page Margins: 1 inch (72 pt) all around
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Base Normal Style: Times New Roman, 12pt
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_table = False
    table_lines = []

    def flush_table(tbl_lines):
        if not tbl_lines:
            return
        # Parse table rows
        rows_data = []
        for tl in tbl_lines:
            stripped = tl.strip()
            if not stripped or stripped.startswith("|---"):
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if any(cells):
                rows_data.append(cells)

        if not rows_data:
            return

        num_cols = max(len(r) for r in rows_data)
        table = doc.add_table(rows=len(rows_data), cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True

        for r_idx, row in enumerate(rows_data):
            is_header = (r_idx == 0)
            for c_idx in range(num_cols):
                val = row[c_idx] if c_idx < len(row) else ""
                # Clean basic markdown bold/italic and clean math
                clean_val = re.sub(r"\*\*(.*?)\*\*", r"\1", val)
                clean_val = re.sub(r"\*(.*?)\*", r"\1", clean_val)
                clean_val = clean_math_text(clean_val)

                cell = table.cell(r_idx, c_idx)
                cell.text = clean_val

                set_cell_margins(cell, top=120, bottom=120, left=160, right=160)

                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1.05
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        if is_header:
                            run.font.size = Pt(10.5)
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        else:
                            run.font.size = Pt(10)
                            run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

                if is_header:
                    set_cell_background(cell, "1E3A8A")
                elif r_idx % 2 == 0:
                    set_cell_background(cell, "F9FAFB")
                else:
                    set_cell_background(cell, "FFFFFF")

        doc.add_paragraph()  # spacing after table

    i = 0
    while i < len(lines):
        line = lines[i]
        raw = line.rstrip("\r\n")
        stripped = raw.strip()

        # Handle Markdown Table Lines
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(raw)
            i += 1
            continue
        elif in_table:
            flush_table(table_lines)
            table_lines = []
            in_table = False

        # Blank lines
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            i += 1
            continue

        # Headings
        if stripped.startswith("# "):
            h_text = clean_math_text(stripped[2:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        elif stripped.startswith("## "):
            h_text = clean_math_text(stripped[3:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(15)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        elif stripped.startswith("### "):
            h_text = clean_math_text(stripped[4:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
        elif stripped.startswith("#### "):
            h_text = clean_math_text(stripped[5:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
        elif stripped.startswith("```"):
            # Code / Math Block
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                clean_code_line = clean_math_text(lines[i].rstrip("\r\n"))
                code_lines.append(clean_code_line)
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run("\n".join(code_lines))
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
        elif stripped.startswith("> "):
            # Blockquote
            quote_text = clean_math_text(stripped[2:].strip())
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(quote_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            # Bullet item
            bullet_text = clean_math_text(stripped[2:].strip())
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            # Parse inline bold
            parts = re.split(r"(\*\*.*?\*\*)", bullet_text)
            for pt in parts:
                if pt.startswith("**") and pt.endswith("**"):
                    r = p.add_run(pt[2:-2])
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
                    r.font.bold = True
                else:
                    r = p.add_run(pt)
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
        elif re.match(r"^\d+\.\s+", stripped):
            # Numbered list
            num_match = re.match(r"^\d+\.\s+", stripped)
            text_part = clean_math_text(stripped[num_match.end():])
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(3)
            parts = re.split(r"(\*\*.*?\*\*)", text_part)
            for pt in parts:
                if pt.startswith("**") and pt.endswith("**"):
                    r = p.add_run(pt[2:-2])
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
                    r.font.bold = True
                else:
                    r = p.add_run(pt)
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
        elif stripped.startswith("![") and "](" in stripped and stripped.endswith(")"):
            # Markdown Image: ![Caption](image_path)
            caption_end = stripped.find("](")
            caption_text = clean_math_text(stripped[2:caption_end].strip())
            rel_path = stripped[caption_end + 2:-1].strip()

            img_path = os.path.normpath(os.path.join(os.path.dirname(md_path), rel_path))
            if os.path.isfile(img_path):
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(2)
                run = p_img.add_run()
                run.add_picture(img_path, width=Inches(6.0))

                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(0)
                p_cap.paragraph_format.space_after = Pt(14)
                cap_run = p_cap.add_run(caption_text)
                cap_run.font.name = "Times New Roman"
                cap_run.font.size = Pt(10)
                cap_run.font.italic = True
                cap_run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
            else:
                print(f"[WARN] Image file not found: {img_path}")
        else:
            # Regular paragraph
            clean_para = clean_math_text(stripped)
            p = doc.add_paragraph()
            parts = re.split(r"(\*\*.*?\*\*)", clean_para)
            for pt in parts:
                if pt.startswith("**") and pt.endswith("**"):
                    r = p.add_run(pt[2:-2])
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
                    r.font.bold = True
                else:
                    r = p.add_run(pt)
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)

        i += 1

    if in_table and table_lines:
        flush_table(table_lines)

    doc.save(docx_path)
    print(f"[SUCCESS] Compiled Clean Human-Math Document: {docx_path}")


if __name__ == "__main__":
    md_file = os.path.join(os.path.dirname(__file__), "CCP_INTERNATIONAL_PROJECT_REPORT.md")
    docx_file = os.path.join(os.path.dirname(__file__), "BioHarvest_Sim_Complex_Computing_Project_Report.docx")
    build_docx_report(md_file, docx_file)
