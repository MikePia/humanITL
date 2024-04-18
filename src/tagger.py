import logging
import os
import json

import fitz  # Import the fitz library
from openai import OpenAI
import pytesseract
from pdf2image import convert_from_path
from bs4 import BeautifulSoup

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_prompt(text):
    sector_options = [
        "Environmental",
        "Technology",
        "Industrials",
        "Basic Materials",
        "Financial Services",
        "Consumer Cyclical",
        "Healthcare",
        "Real Estate",
        "Communication Services",
        "Utilities",
        "Energy",
        "Consumer Defensive",
        "Industrial",  # Assuming 'Industrial' is distinct from 'Industrials'
        "Other",
    ]

    # Define the system message with better formatting and clarity
    system_message = (
        "You will analyze the text from the first page of an Investor Presentation document. "
        "Extract the specific information and return the result as a JSON object with keys: 'title', 'author', 'date', and 'sector'. "
        f"Identify the sector from the following list: {', '.join(sector_options)}. "
        "If none of the specific sectors seem to apply, select 'Other' and provide an educated guess after the colon (e.g., 'Other:<guess>'). "
        "If the text does not contain any of the requested information, leave the corresponding value blank."
    )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": text},
    ]

    return messages


def use_ocr(pdf_path):
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1)

        # Since there's only one page, we take the first image from the list
        if images:
            image = images[0]
            # Perform OCR using Tesseract
            text = pytesseract.image_to_string(image)
            return text
        else:
            return ""

    except Exception as e:
        logger.error(f"Tesseract error processing PDF: {e}")
        return ""


def use_fitz(pdf_path):
    if not os.path.exists(pdf_path):
        return ""
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0]
        text = first_page.get_text()
        return text

    except Exception as e:
        logger.error(f"Fitz Error opening PDF file: {e}")
        return ""
    finally:
        doc.close()




def askgpt_html(html_content):
    """
    Analyze the text from the initial content of an HTML document obtained via Selenium and extract specific information.
    """
    MAXLEN = 2000
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extracting text from certain tags, considering them as indicative of initial content
        text_parts = []
        for tag in soup.find_all(['h1', 'h2', 'p'], limit=10):  # Adjust the limit and tags as per your HTML structure
            if tag.text:
                text_parts.append(tag.text.strip())
        text = ' '.join(text_parts)
        
        # Check if the extracted text is too long
        if len(text) > MAXLEN:
            text = ""
            logging.error(f"Extracted HTML text is too long to be a presentation title page. Length: {len(text)}")
        
        if not text:
            return None

        messages = create_prompt(text)

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4-turbo",
            temperature=0.5,
        )

        result = json.loads(chat_completion.choices[0].message.content)
        return result
    except Exception as e:
        logging.error(f"Error processing HTML content with BeautifulSoup or OpenAI: {e}")
        return ""

# Example of using this function
# driver.get(url)
# html_content = driver.page_source
# result = askgpt_html(html_content)


def askgpt(pdf_path):
    """
    Analyze the text from the first page of a PDF document and extract specific information.
    """
    MAXLEN = 2000
    try:
        text1 = use_fitz(pdf_path)
        text2 = use_ocr(pdf_path)
        # sanity check. If this is a presentation title page, It will not be longer than MAXLEN characters (safeguess here)
        if len(text1) > MAXLEN: 
            text1 = ""
            logger.error(f"Text from fitz is too long to be a presentation title page. ({len(text1)})")
        if len(text2) > MAXLEN:
            text2 = ""
            logger.error(f"Text from tesseract ocr is too long to be a presentation title page., ({len(text2)})")

        text = text1 + text2
        if not text:
            return None

        messages = create_prompt(text)

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4-turbo",
            temperature=0.5,
        )

        result = json.loads(chat_completion.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error processing PDF with fitx, tesseract, or openai: {e}")
        return ""

