import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from django.core.files.base import ContentFile

def create_certificate_pdf(student_name, course_title, date_str, cert_id):
    """
    Generates an A4 landscape certificate PDF.
    Expects a blank 'certificate_bg.jpg' to be placed in the media folder eventually.
    """
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file."
    # A4 landscape is exactly 841.89 x 595.27 points
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # If you have a background image, you would draw it here:
    # bg_path = os.path.join(settings.MEDIA_ROOT, 'certificate_bg.jpg')
    # if os.path.exists(bg_path):
    #     p.drawImage(bg_path, 0, 0, width=width, height=height)
    
    # -----------------------------------------------------
    # TEMPORARY TEXT FALLBACK (until background is uploaded)
    # -----------------------------------------------------
    p.setFont("Helvetica-Bold", 36)
    p.drawCentredString(width / 2.0, height - 150, "CERTIFICATE OF ACHIEVEMENT")
    
    p.setFont("Helvetica", 18)
    p.drawCentredString(width / 2.0, height - 200, "PROUDLY PRESENTED TO")
    
    p.setFont("Helvetica-Oblique", 48) # Cursive placeholder
    p.drawCentredString(width / 2.0, height - 280, student_name)
    
    p.setFont("Helvetica", 14)
    description = f"Congratulations on completing the {course_title} course!"
    p.drawCentredString(width / 2.0, height - 350, description)
    p.drawCentredString(width / 2.0, height - 370, "Your dedication and hard work have paid off.")
    
    # Signatures
    p.setFont("Helvetica-Bold", 14)
    p.drawString(150, height - 480, "Coach Izu")
    p.setFont("Helvetica", 10)
    p.drawString(150, height - 500, "Signature")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(width - 250, height - 480, date_str)
    p.setFont("Helvetica", 10)
    p.drawString(width - 250, height - 500, "Date")

    # ID
    p.setFont("Helvetica", 8)
    p.drawString(30, 30, f"Verify: learnxacademy.com/verify/{cert_id}")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    
    return ContentFile(pdf)
