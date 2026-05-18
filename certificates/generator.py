import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.core.files.base import ContentFile


def create_certificate_pdf(student_name, course_title, date_str, cert_id):
    """
    Generates an A4 landscape certificate PDF.
    """
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    from django.conf import settings
    from reportlab.lib.colors import HexColor

    # Draw the background image
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'certificate_bg.png')
    if os.path.exists(bg_path):
        p.drawImage(bg_path, 0, 0, width=width, height=height)
    else:
        # Fallback if image missing
        p.setFont("Helvetica-Bold", 36)
        p.drawCentredString(width / 2.0, height - 150, "CERTIFICATE OF ACHIEVEMENT")
    
    # Student Name (above the center line) — bold hand-drawn uppercase style
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'PermanentMarker-Regular.ttf')
    font_loaded = False
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('PermanentMarker', font_path))
            p.setFont("PermanentMarker", 30)
            font_loaded = True
        except Exception as e:
            print(f"Failed to load custom font: {e}")
            
    if not font_loaded:
        p.setFont("Helvetica-Bold", 36)
        
    p.setFillColor(HexColor("#1e40af")) # Brand Blue
    display_name = student_name.upper()
    p.drawCentredString(width / 2.0, height / 2.0 + 20, display_name)
    
    # Course Title (below "has completed")
    p.setFont("Helvetica-Bold", 28)
    p.setFillColor(HexColor("#1e3a8a")) # Blue
    p.drawCentredString(width / 2.0, height / 2.0 - 90, course_title)
    
    # Richer writeup below the course title
    p.setFont("Helvetica", 14)
    p.setFillColor(HexColor("#1e3a8a")) # Dark blue to match title
    p.drawCentredString(width / 2.0, height / 2.0 - 130, "having met all academic requirements and demonstrated")
    p.drawCentredString(width / 2.0, height / 2.0 - 150, "outstanding proficiency in the subject matter.")
    
    # Date (above the left DATE line)
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(HexColor("#1e40af")) # Brand Blue
    # Centered precisely over the DATE line
    p.drawCentredString(width * 0.265, 72, date_str)
    
    # Certificate ID (Top right stamped style)
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

    # A4 landscape at 150 DPI: 1754 x 1240 px. Use 1024x724 to match template.
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

    # Load Permanent Marker font
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'PermanentMarker-Regular.ttf')
    try:
        name_font = ImageFont.truetype(font_path, 38)
    except Exception:
        try:
            name_font = ImageFont.truetype("arial.ttf", 38)
        except Exception:
            name_font = ImageFont.load_default()

    # Load system fonts for other text
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 32)
        body_font = ImageFont.truetype("arial.ttf", 16)
        date_font = ImageFont.truetype("arialbd.ttf", 16)
        id_font = ImageFont.truetype("cour.ttf", 14)
    except Exception:
        try:
            title_font = ImageFont.truetype("arial.ttf", 32)
            body_font = ImageFont.truetype("arial.ttf", 16)
            date_font = ImageFont.truetype("arial.ttf", 16)
            id_font = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
            id_font = ImageFont.load_default()

    # --- Draw text at positions matching the PDF layout ---
    # PDF coordinate system: origin bottom-left. Pillow: origin top-left.
    # PDF page: 842 x 595. Template image: img_w x img_h.
    # Scale factors:
    sx = img_w / 842.0
    sy = img_h / 595.0

    # Helper: convert PDF coords (origin bottom-left) to Pillow coords (origin top-left)
    def pdf_to_pil(pdf_x, pdf_y):
        return (pdf_x * sx, (595 - pdf_y) * sy)

    # Student Name — PDF: drawCentredString(width/2, height/2 + 20)
    display_name = student_name.upper()
    name_bbox = draw.textbbox((0, 0), display_name, font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]
    nx, ny = pdf_to_pil(421, 297.5 + 20)
    draw.text((nx - name_w / 2, ny - name_h / 2), display_name, font=name_font, fill=brand_blue)

    # Course Title — PDF: drawCentredString(width/2, height/2 - 90)
    title_bbox = draw.textbbox((0, 0), course_title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    tx, ty = pdf_to_pil(421, 297.5 - 90)
    draw.text((tx - title_w / 2, ty - title_h / 2), course_title, font=title_font, fill=dark_blue)

    # Body text line 1 — PDF: drawCentredString(width/2, height/2 - 130)
    line1 = "having met all academic requirements and demonstrated"
    l1_bbox = draw.textbbox((0, 0), line1, font=body_font)
    l1_w = l1_bbox[2] - l1_bbox[0]
    l1x, l1y = pdf_to_pil(421, 297.5 - 130)
    draw.text((l1x - l1_w / 2, l1y), line1, font=body_font, fill=dark_blue)

    # Body text line 2 — PDF: drawCentredString(width/2, height/2 - 150)
    line2 = "outstanding proficiency in the subject matter."
    l2_bbox = draw.textbbox((0, 0), line2, font=body_font)
    l2_w = l2_bbox[2] - l2_bbox[0]
    l2x, l2y = pdf_to_pil(421, 297.5 - 150)
    draw.text((l2x - l2_w / 2, l2y), line2, font=body_font, fill=dark_blue)

    # Date — PDF: drawCentredString(width * 0.265, 72)
    d_bbox = draw.textbbox((0, 0), date_str, font=date_font)
    d_w = d_bbox[2] - d_bbox[0]
    dx, dy = pdf_to_pil(842 * 0.265, 72)
    draw.text((dx - d_w / 2, dy), date_str, font=date_font, fill=brand_blue)

    # Certificate ID — PDF: drawRightString(width - 120, height - 40)
    short_id = str(cert_id)[:8].upper()
    id_text = f"CERT NO: {short_id}"
    id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
    id_w = id_bbox[2] - id_bbox[0]
    idx, idy = pdf_to_pil(842 - 120, 595 - 40)
    draw.text((idx - id_w, idy), id_text, font=id_font, fill=slate_gray)

    # Convert to RGB and save as JPEG for smaller file size
    img_rgb = img.convert('RGB')
    buffer = BytesIO()
    img_rgb.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer
