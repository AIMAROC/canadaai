import requests
import pandas as pd
from tqdm import tqdm
import re
import pdfplumber
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTRect
from typing import List, Dict, Optional
import google.generativeai as genai
import random
import json
import logging
import os
import requests
import pandas as pd
from tqdm import tqdm
import re
import pdfplumber
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTRect
from typing import List, Dict, Optional, Union
import google.generativeai as genai
import random
import json
import logging
import os
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, pdf_path: str, model_name: str):
        self.pdf_path = pdf_path
        self.model_name = model_name
        logger.info("PDFProcessor initialized with pdf_path: %s and model_name: %s", pdf_path, model_name)

    def process_document(self, text: bool = True, table: bool = True, page_ids: Optional[List[int]] = None) -> Dict[int, str]:
        logger.info("Processing document: %s", self.pdf_path)
        with pdfplumber.open(self.pdf_path) as pdf:
            pages = pdf.pages
            total_pages = len(pages)

            if page_ids is None:
                page_ids = list(range(total_pages))
            
            extracted_pages = extract_pages(self.pdf_path, page_numbers=page_ids)
            page2content = {}

            for extracted_page in tqdm(extracted_pages, desc="Processing pages"):
                page_id = extracted_page.pageid
                logger.debug("Processing page: %d", page_id)
                content = self._process_page(pages[page_id - 1], extracted_page, text, table)
                page2content[page_id] = content

        logger.info("Document processing complete")
        return page2content

    def _process_page(self, page, extracted_page, text: bool = True, table: bool = True) -> str:
        logger.debug("Processing individual page")
        content = []
        tables = page.find_tables()
        extracted_tables = page.extract_tables()
        
        table_num = 0
        first_table_element = True
        table_extraction_process = False

        elements = sorted([element for element in extracted_page._objs], key=lambda a: -a.y1)

        lower_side = 0
        upper_side = 0
        for i, element in enumerate(elements):
            if isinstance(element, LTTextContainer) and not table_extraction_process and text:
                line_text = self._text_extraction(element)
                content.append(line_text)

            if isinstance(element, LTRect) and table:
                if first_table_element and table_num < len(tables):
                    lower_side = page.bbox[3] - tables[table_num].bbox[3]
                    upper_side = element.y1

                    table_data = extracted_tables[table_num]
                    table_string = self._convert_table(table_data)
                    content.append(table_string)
                    table_extraction_process = True
                    first_table_element = False

                if lower_side <= element.y0 <= upper_side:
                    continue
                elif i + 1 >= len(elements) or not isinstance(elements[i + 1], LTRect):
                    table_extraction_process = False
                    first_table_element = True
                    table_num += 1

        content = re.sub('\n+', '\n', ''.join(content))
        return content

    @staticmethod
    def _normalize_text(line_texts: List[str]) -> str:
        return ' '.join(' '.join(line_texts).split())

    def _text_extraction(self, element) -> str:
        line_texts = element.get_text().split('\n')
        return self._normalize_text(line_texts)

    @staticmethod
    def _convert_table(table: List[List[str]]) -> str:
        return '\n'.join(['|' + '|'.join(
            'None' if item is None else item.replace('\n', ' ') for item in row
        ) + '|' for row in table])


    def get_gemini_response(self, user_input: str, prompt: str, context: str, history: List[Dict[str, str]]) -> str:
        logger.info("Getting Gemini response for user input: %s", user_input)
        generation_config = {
            "temperature": 0.2,  # Reduced temperature for more deterministic output
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        model = genai.GenerativeModel(model_name=self.model_name, generation_config=generation_config)

        formatted_history = [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg.get("parts", [msg.get("content", "")])[0]]}
            for msg in history
        ]

        chat_session = model.start_chat(history=formatted_history)
        full_prompt = f"{prompt}\n\nDocument content:\n{context}\n\nUser question: {user_input}\n\nAnswer in a clear, tabular format with headers: "

        response = chat_session.send_message(full_prompt).text
        logger.info("Gemini response received")
        logger.debug("Raw Gemini response: %s", response)
        
        return response

    def extract_table_from_text(self, text: str) -> List[List[str]]:
        # Split the text into lines and remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Identify the delimiter (assuming it's consistent throughout the text)
        delimiters = ['|', '\t', ',']
        delimiter = max(delimiters, key=lambda d: text.count(d))
        
        # Split each line by the delimiter and strip whitespace from each cell
        table = [
            [cell.strip() for cell in line.split(delimiter) if cell.strip()]
            for line in lines
        ]
        
        return table

    def construct_table(self, text: str, columns: Optional[List[str]], user_input: str, prompt: str, context: str, history: List[Dict[str, str]]) -> pd.DataFrame:
        logger.info("Constructing table")
        response_data = self.get_gemini_response(user_input, prompt, context, history)
        
        # Attempt to extract a table from the raw text response
        table_data = self.extract_table_from_text(response_data)
        
        if table_data:
            if columns:
                table = pd.DataFrame(table_data[1:], columns=columns)
            else:
                table = pd.DataFrame(table_data[1:], columns=table_data[0])
        else:
            logger.error("Failed to extract tabular data from the response")
            table = pd.DataFrame()

        logger.info("Table constructed")
        return table

def main():
    pdf_path = './data/financial_report.pdf'
    KEYS = ["AIzaSyBkTJsctYOkljL0tx-6Y8NwYCaSz-r0XmU", "AIzaSyDbzt8ZGVd3P15MMuIUh8wz1lzT5jRLWlc"]
    MODEL_NAME = "gemini-1.5-flash"
    UPLOAD_DIR = "uploads"

    # Configure genai
    genai.configure(api_key=random.choice(KEYS))

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    processor = PDFProcessor(pdf_path, MODEL_NAME)
    page2content = processor.process_document(page_ids=[0, 1])

    user_input = "Extract all relevant information and format it as a table"
    prompt = "Based on the provided document content, create a comprehensive table summarizing the key information. The table should have clear headers and organized rows. Present the information in a plain text format, using '|' as a delimiter between columns. Ensure each row of data is on a new line."
    context = '\n'.join(page2content.values())
    history = []

    table = processor.construct_table(context, None, user_input, prompt, context, history)
    
    output_file = os.path.join(UPLOAD_DIR, 'pfizer_products_summary.csv')
    table.to_csv(output_file, index=False)
    logger.info(f"Table saved to {output_file}")
    logger.info(f"Table preview:\n{table.head().to_string()}")

if __name__ == "__main__":
    main()
