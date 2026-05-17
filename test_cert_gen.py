import os
import django
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor

# Setup minimal django settings to test standalone
import sys
sys.path.append(r'c:\Users\USER\Documents\Learnx')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

def create_test_pdf():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'certificate_bg.png')
    if os.path.exists(bg_path):
        p.drawImage(bg_path, 0, 0, width=width, height=height)
    
    student_name = "efirmzylaff@gmail.com"
    course_title = "ChatGPT Complete Mastery"
    date_str = "May 16, 2026"
    cert_id = "f27b7c71-dd16-4ad2-9154-a6ab12233975"
    
    # Coordinates to adjust
    # Student Name (on the line)
    p.setFont("Helvetica-Bold", 32)
    p.setFillColor(HexColor("#0f172a")) # Dark slate
    p.drawCentredString(width / 2.0, height / 2.0 + 20, student_name)
    
    # Course Title
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(HexColor("#1e3a8a")) # Blue
    p.drawCentredString(width / 2.0, height / 2.0 - 80, course_title)
    
    # Date (bottom left)
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(HexColor("#0f172a"))
    p.drawCentredString(230, 80, date_str)
    
    # Verify ID (bottom right)
    p.setFont("Helvetica", 8)
    p.setFillColor(HexColor("#64748b"))
    p.drawRightString(width - 40, 20, f"Verify: www.bluedemy.org/verify/{cert_id}")
    
    p.showPage()
    p.save()
    
    with open('test_cert.pdf', 'wb') as f:
        f.write(buffer.getvalue())

if __name__ == "__main__":
    create_test_pdf()
    print("test_cert.pdf generated!")
