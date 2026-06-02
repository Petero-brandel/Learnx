import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
import logging

logger = logging.getLogger(__name__)
from django.core.files.base import ContentFile
from reportlab.lib.colors import HexColor


def create_certificate_pdf(student_name, course_title, date_str, cert_id):
    """
    Generates an A4 landscape certificate PDF.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    from django.conf import settings
    
    # Background
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'certificate_bg.png')
    if os.path.exists(bg_path):
        p.drawImage(bg_path, 0, 0, width=width, height=height)
    
    # Student Name
    p.setFont("Times-Bold", 38)
    p.setFillColor(HexColor("#1e40af"))
    display_name = student_name.upper()
    name_y = height / 2.0 + 17.6
    p.drawCentredString(width / 2.0, name_y, display_name)
    
    # Course Title
    p.setFont("Helvetica-Bold", 28)
    p.setFillColor(HexColor("#1e3a8a"))
    p.drawCentredString(width / 2.0, height / 2.0 - 90, course_title)
    
    # ================== BODY TEXT (Moved DOWN 10 points) ==================
    p.setFont("Helvetica", 14)
    p.setFillColor(HexColor("#1e3a8a"))
    p.drawCentredString(width / 2.0, height / 2.0 - 115, "having met all academic requirements and demonstrated")
    p.drawCentredString(width / 2.0, height / 2.0 - 135, "outstanding proficiency in the subject matter.")
    
    # Date
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(HexColor("#1e40af"))
    p.drawCentredString(width * 0.265, 72, date_str)
    
    # Certificate ID
    p.setFont("Courier-Bold", 12)
    p.setFillColor(HexColor("#64748b"))
    short_id = str(cert_id)[:8].upper()
    p.drawRightString(width - 120, height - 40, f"CERT NO: {short_id}")

    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf)


def create_certificate_preview(student_name, course_title, date_str, cert_id):
    """
    Generates a PNG preview image of the certificate using Pillow.
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
    brand_blue = (30, 64, 175)
    dark_blue = (30, 58, 138)
    slate_gray = (100, 116, 139)

    # Fonts
    try:
        name_font = ImageFont.truetype("timesbd.ttf", 38)
    except:
        try:
            name_font = ImageFont.truetype("arialbd.ttf", 38)
        except:
            name_font = ImageFont.load_default()

    try:
        title_font = ImageFont.truetype("arialbd.ttf", 28)
        body_font = ImageFont.truetype("arial.ttf", 14)
        date_font = ImageFont.truetype("arialbd.ttf", 14)
        id_font = ImageFont.truetype("cour.ttf", 12)
    except:
        title_font = body_font = date_font = id_font = ImageFont.load_default()

    sx = img_w / 842.0
    sy = img_h / 595.0

    def draw_text_centered_baseline(text, pdf_x, pdf_y, font, fill):
        px = pdf_x * sx
        py_baseline = (595 - pdf_y) * sy
        tb = draw.textbbox((0, 0), text, font=font)
        text_w = tb[2] - tb[0]
        ascent = tb[3] - tb[1]
        top_left_x = px - text_w / 2
        top_left_y = py_baseline - ascent
        draw.text((top_left_x, top_left_y), text, font=font, fill=fill)

    def draw_text_right_baseline(text, pdf_x, pdf_y, font, fill):
        px = pdf_x * sx
        py_baseline = (595 - pdf_y) * sy
        tb = draw.textbbox((0, 0), text, font=font)
        text_w = tb[2] - tb[0]
        ascent = tb[3] - tb[1]
        top_left_x = px - text_w
        top_left_y = py_baseline - ascent
        draw.text((top_left_x, top_left_y), text, font=font, fill=fill)

    # Student Name
    display_name = student_name.upper()
    draw_text_centered_baseline(display_name, 421, 297.5 + 17.6, name_font, brand_blue)

    # Course Title
    draw_text_centered_baseline(course_title, 421, 297.5 - 90, title_font, dark_blue)

    # ================== BODY TEXT (Moved DOWN 10 points) ==================
    draw_text_centered_baseline("having met all academic requirements and demonstrated", 
                               421, 297.5 - 115, body_font, dark_blue)
    draw_text_centered_baseline("outstanding proficiency in the subject matter.", 
                               421, 297.5 - 135, body_font, dark_blue)

    # Date
    draw_text_centered_baseline(date_str, 842 * 0.265, 72, date_font, brand_blue)
    
    # Certificate ID
    short_id = str(cert_id)[:8].upper()
    draw_text_right_baseline(f"CERT NO: {short_id}", 842 - 120, 595 - 40, id_font, slate_gray)

    # Save preview
    img_rgb = img.convert('RGB')
    buffer = BytesIO()
    img_rgb.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer