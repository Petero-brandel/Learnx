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
    Expects a blank 'certificate_bg.jpg' to be placed in the media folder eventually.
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
    
    # Student Name (above the center line)
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'GreatVibes-Regular.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('GreatVibes', font_path))
        p.setFont("GreatVibes", 56) # Slightly reduced so tall capitals don't overlap the text above
    else:
        p.setFont("Helvetica-Bold", 36)
        
    p.setFillColor(HexColor("#1e40af")) # Brand Blue
    p.drawCentredString(width / 2.0, height / 2.0 + 20, student_name) # Positioned perfectly between the text and the line
    
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
    # Centered over the DATE line (approx 1/4 page width)
    p.drawCentredString(width * 0.235, 72, date_str)
    
    # Certificate ID (Top right stamped style)
    p.setFont("Courier-Bold", 12)
    p.setFillColor(HexColor("#64748b")) # Slate gray
    short_id = cert_id[:8].upper()
    p.drawRightString(width - 40, height - 40, f"CERT NO: {short_id}")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    
    return ContentFile(pdf)
