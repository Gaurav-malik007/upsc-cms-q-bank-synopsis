import fitz
import sys

def peek_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        print(f"Total pages: {len(doc)}")
        for page_num in range(min(5, len(doc))):
            print(f"--- Page {page_num+1} ---")
            page = doc.load_page(page_num)
            text = page.get_text()
            print(text[:1000]) # First 1000 chars
            print("\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    peek_pdf(r"c:\Users\deepa\Desktop\cms\pyq pdf\Upsc cms 2025 paper 1.pdf")
