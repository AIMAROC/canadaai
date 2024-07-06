import fitz  # PyMuPDF
import pdfplumber
import pytesseract
import pandas as pd
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image
import os

class OCRProcessor:
    def __init__(self, tessdata_dir='', lang='ara'):
        self.set_tessdata_prefix(tessdata_dir)
        self.lang = lang

    def set_tessdata_prefix(self, tessdata_dir):
        os.environ["TESSDATA_PREFIX"] = tessdata_dir
        print(f"TESSDATA_PREFIX set to: {os.getenv('TESSDATA_PREFIX')}")

    def process_image(self, image_path):
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file '{image_path}' not found.")
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text
        except Exception as e:
            print(f"Error processing image: {e}")
            return None

# Function to reshape and display Arabic text correctly
def reshape_text(text):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

# Function to extract tables from a PDF file
def extract_tables_from_pdf(pdf_path, start_page, end_page):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, end_page):
            page = pdf.pages[page_num]
            for table in page.extract_tables():
                tables.extend(table)
    return tables

# Function to process and save tables to a CSV file
def process_and_save_tables(tables, csv_path):
    # Convert tables to DataFrame
    df = pd.DataFrame(tables)
    # Reshape Arabic text
    for col in df.columns:
        df[col] = df[col].apply(lambda x: reshape_text(x) if isinstance(x, str) else x)
    # Save to CSV
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

# Main function
def main():
    pdf_path = './test2.pdf'
    image_path = './test.jpg'
    csv_path = 'output_file.csv'
    extracted_text_path = 'extracted_text.txt'
    start_page = 1
    end_page = 4
    
    # Initialize OCR processor
    ocr_processor = OCRProcessor(tessdata_dir='.', lang='ara')
    
    # Extract tables from PDF
    tables = extract_tables_from_pdf(pdf_path, start_page, end_page)
    
    # Process and save tables to CSV
    process_and_save_tables(tables, csv_path)
    print(f"Data successfully saved to {csv_path}")
    
    # Process image and print text
    extracted_text = ocr_processor.process_image(image_path)
    if extracted_text:
        print("Extracted Text from Image:")
        #print(extracted_text)
        
        # Save extracted text to a file
        with open(extracted_text_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        print(f"Extracted text successfully saved to {extracted_text_path}")

if __name__ == "__main__":
    main()
