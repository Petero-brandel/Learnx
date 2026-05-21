import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    font_path = r"c:\Users\USER\Documents\Learnx\static\fonts\DancingScript-Bold.ttf"
    print(f"Font size: {os.path.getsize(font_path)}")
    pdfmetrics.registerFont(TTFont('DancingScript', font_path))
    print("Font loaded successfully!")
except Exception as e:
    print(f"Error loading font: {e}")
