import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

logger = logging.getLogger(__name__)
from django.core.files.base import ContentFile


def create_certificate_pdf(student_name, course_title, date_str, cert_id):
    """
    Generates an A4 landscape certificate PDF.
    """
    buffer = BytesIO()
    
    # PDF canvas
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    from django.conf import settings
    from reportlab.lib.colors import HexColor
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'certificate_bg.png')
    if os.path.exists(bg_path):
        p.drawImage(bg_path, 0, 0, width=width, height=height)
    else:
        p.setFont("Helvetica-Bold", 36)
        p.drawCentredString(width / 2.0, height - 150, "CERTIFICATE OF ACHIEVEMENT")
    p.setFont("Times-Bold", 40)
    p.setFillColor(HexColor("#1e40af")) # Brand Blue
    display_name = (student_name or "").strip()
    if not display_name:
        display_name = "There"
    display_name = display_name.upper()
    p.drawCentredString(width / 2.0, height / 2.0 - 10, display_name)
    p.setFont("Helvetica-Bold", 28)
    p.setFillColor(HexColor("#1e3a8a")) # Blue
    p.drawCentredString(width / 2.0, height / 2.0 - 90, course_title)
    p.setFont("Helvetica", 14)
    p.setFillColor(HexColor("#1e3a8a")) # Dark blue to match title
    p.drawCentredString(width / 2.0, height / 2.0 - 130, "having met all academic requirements and demonstrated")
    p.drawCentredString(width / 2.0, height / 2.0 - 150, "outstanding proficiency in the subject matter.")
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(HexColor("#1e40af")) # Brand Blue
    # Centered precisely over the DATE line
    p.drawCentredString(width * 0.265, 72, date_str)
    p.setFont("Courier-Bold", 12)
    p.setFillColor(HexColor("#64748b")) # Slate gray
    short_id = str(cert_id)[:8].upper()
    p.drawRightString(width - 120, height - 40, f"CERT NO: {short_id}")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    
    return ContentFile(pdf)


def create_certificate_preview(student_name, course_title, date_str, cert_id):
    """
    Generates a PNG preview image of the certificate using Pillow.
    Mirrors the exact same layout as the PDF generator.
    """
    from PIL import Image, ImageDraw, ImageFont
    from django.conf import settings
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'certificate_bg.png')
    if os.path.exists(bg_path):
        img = Image.open(bg_path).convert('RGBA')
    else:
        img = Image.new('RGBA', (1024, 724), (255, 255, 255, 255))
    img_w, img_h = img.size
    draw = ImageDraw.Draw(img)

    # Colors
    brand_blue = (30, 64, 175)     # #1e40af
    dark_blue = (30, 58, 138)      # #1e3a8a
    slate_gray = (100, 116, 139)   # #64748b
    # Load Times New Roman font (sizes chosen to match PDF generator)
    try:
        name_font = ImageFont.truetype("timesbd.ttf", 36)
    except Exception:
        try:
            name_font = ImageFont.truetype("times.ttf", 36)
        except Exception:
            try:
                name_font = ImageFont.truetype("arialbd.ttf", 36)
            except Exception:
                name_font = ImageFont.load_default()
    # Load system fonts for other text
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 28)
        body_font = ImageFont.truetype("arial.ttf", 14)
        date_font = ImageFont.truetype("arialbd.ttf", 14)
        id_font = ImageFont.truetype("cour.ttf", 12)
    except Exception:
        try:
            title_font = ImageFont.truetype("arial.ttf", 28)
            body_font = ImageFont.truetype("arial.ttf", 14)
            date_font = ImageFont.truetype("arial.ttf", 14)
            id_font = ImageFont.truetype("arial.ttf", 12)
        except Exception:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
            id_font = ImageFont.load_default()
    # --- Draw text at positions matching the PDF layout ---
    # Scale factors:
    sx = img_w / 842.0
    sy = img_h / 595.0
    # Helper: convert PDF coords (origin bottom-left) to Pillow coords (origin top-left)
    def pdf_to_pil(pdf_x, pdf_y):
        return (pdf_x * sx, (595 - pdf_y) * sy)
    # Helper: draw text centered horizontally at a PDF baseline y (reportlab uses baseline)
    def draw_text_centered_baseline(text, pdf_x, pdf_y, font, fill):
        px = pdf_x * sx
        py_baseline = (595 - pdf_y) * sy
        try:
            ascent, descent = font.getmetrics()
        except Exception:
            # Fallback: approximate ascent from bbox
            tb = draw.textbbox((0, 0), text, font=font)
            ascent = tb[3] - tb[1]
        tb = draw.textbbox((0, 0), text, font=font)
        text_w = tb[2] - tb[0]
        top_left_x = px - text_w / 2
        top_left_y = py_baseline - ascent
        draw.text((top_left_x, top_left_y), text, font=font, fill=fill)

    # Helper: draw text right-aligned to a PDF baseline y
    def draw_text_right_baseline(text, pdf_x, pdf_y, font, fill):
        px = pdf_x * sx
        py_baseline = (595 - pdf_y) * sy
        try:
            ascent, descent = font.getmetrics()
        except Exception:
            tb = draw.textbbox((0, 0), text, font=font)
            ascent = tb[3] - tb[1]
        tb = draw.textbbox((0, 0), text, font=font)
        text_w = tb[2] - tb[0]
        top_left_x = px - text_w
        top_left_y = py_baseline - ascent
        draw.text((top_left_x, top_left_y), text, font=font, fill=fill)

    # Student Name — align to PDF baseline used in create_certificate_pdf
    display_name = (student_name or "").strip()
    if not display_name:
        display_name = "There"
    display_name = display_name.upper()
    # PDF used: drawCentredString(width/2.0, height/2.0 - 10)
    # Move the name up slightly and reduce font size so it sits above the line
    draw_text_centered_baseline(display_name, 421, 297.5 + 12, name_font, brand_blue)

    # Course Title — align to baseline like PDF (drawCentredString)
    draw_text_centered_baseline(course_title, 421, 297.5 - 90, title_font, dark_blue)
    # Body text line 1 & 2 — align to baselines used in PDF
    line1 = "having met all academic requirements and demonstrated"
    line2 = "outstanding proficiency in the subject matter."
    draw_text_centered_baseline(line1, 421, 297.5 - 130, body_font, dark_blue)
    draw_text_centered_baseline(line2, 421, 297.5 - 150, body_font, dark_blue)
    # Date — center on PDF baseline at y=72
    draw_text_centered_baseline(date_str, 842 * 0.265, 72, date_font, brand_blue)
    # Certificate ID — PDF: drawRightString(width - 120, height - 40)
    short_id = str(cert_id)[:8].upper()
    id_text = f"CERT NO: {short_id}"
    # Certificate ID — right-aligned to PDF baseline used in PDF generator
    draw_text_right_baseline(id_text, 842 - 120, 595 - 40, id_font, slate_gray)

    # Convert to RGB and save as JPEG for smaller file size
    img_rgb = img.convert('RGB')
    buffer = BytesIO()
    img_rgb.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer
