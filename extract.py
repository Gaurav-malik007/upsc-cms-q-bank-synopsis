import fitz
import pytesseract
from PIL import Image
import io

# If you install Tesseract-OCR, you may need to point pytesseract to it:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(pdf_path, start_page=2, end_page=4):
    doc = fitz.open(pdf_path)
    text = ""
    for i in range(start_page, min(end_page + 1, len(doc))):
        page = doc.load_page(i)
        text += f"\n--- PAGE {i} ---\n"
        
        # 1. Try standard embedded text extraction first
        page_text = page.get_text("text")
        
        # 2. If no text is found, or if you want to force OCR, we render it as an image
        if len(page_text.strip()) < 50:  # Arbitrary threshold to detect "image-only" pages
            print(f"Page {i} seems to be an image. Running OCR...")
            
            # Render page to an image (dpi=300 for good OCR quality)
            zoom = 300 / 72  
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert PyMuPDF pixmap to a Pillow Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Run OCR on the image
            ocr_text = pytesseract.image_to_string(img)
            text += ocr_text
        else:
            text += page_text
            
    print(text[:3000])

if __name__ == "__main__":
    extract_text("upsc cms 2024 paper 1.pdf")
