import json
import logging
import os

import fitz  # Import the fitz library
from openai import OpenAI
import pytesseract
from pdf2image import convert_from_path
import pandas as pd

from predict_title_page import predict_title_page


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)


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


def use_ocr(pdf_path, target_page=1):
    """
    Extract text from a specific page of a PDF using OCR.

    :param pdf_path: Path to the PDF file.
    :param target_page: The page number to perform OCR on.
    :return: Extracted text as a string, or an empty string if an error occurs or no text is found.
    """
    try:
        # Convert only the target page
        images = convert_from_path(
            pdf_path, first_page=target_page, last_page=target_page
        )

        # Since we're extracting a specific page, take the first image from the list
        if images:
            image = images[0]
            # Perform OCR using Tesseract
            text = pytesseract.image_to_string(image)
            return text
        else:
            return ""

    except Exception as e:
        logger.error(f"Tesseract error processing PDF on page {target_page}: {e}")
        return ""


def use_fitz(pdf_path, target_page=1):
    if not os.path.exists(pdf_path):
        return ""
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[target_page - 1]
        text = first_page.get_text()
        return text

    except Exception as e:
        logger.error(f"Fitz Error opening PDF file: {e}")
        return ""
    finally:
        doc.close()


# Example of using this function
# driver.get(url)
# html_content = driver.page_source
# result = askgpt_html(html_content)


def askgpt(pdf_path) -> dict | None:
    """
    Analyze the text from the first page of a PDF document and extract specific information.
    """
    MAXLEN = 2000
    try:
        text1 = use_fitz(pdf_path)
        text2 = use_ocr(pdf_path)
        # sanity check. If this is a presentation title page, It will not be longer than MAXLEN characters (safeguess here)
        # But let's put in the first thousand characters in order to try to get some meaningful result
        if len(text1) > MAXLEN:
            text1 = text1[:MAXLEN]
            logger.error(
                f"Text from fitz is too long to be a presentation title page. ({len(text1)})"
            )
        if len(text2) > MAXLEN:
            text2 = text2[:MAXLEN]
            logger.error(
                f"Text from tesseract ocr is too long to be a presentation title page., ({len(text2)})"
            )

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
        return None


def askgpt_mix(pdf_path) -> dict | None:
    """
    This function assumes the investor presentation title page might start later in the document.
    It identifies the potential title page and then processes it to extract the required information.
    """
    if not os.path.exists(pdf_path):
        logger.error("PDF path does not exist.")
        return None

    try:
        doc = fitz.open(pdf_path)
        tp_num = predict_title_page(doc)

        if not tp_num:
            logger.error("Failed to find a title page in the document.")
            return None

        MAXLEN = 2000

        text1 = use_fitz(pdf_path, target_page=tp_num)
        text2 = use_ocr(pdf_path, target_page=tp_num)
        # sanity check. If this is a presentation title page, It will not be longer than MAXLEN characters (safeguess here)
        # But let's put in the first thousand characters in order to try to get some meaningful result
        if len(text1) > MAXLEN:
            text1 = text1[:MAXLEN]
            logger.error(
                f"Text from fitz is too long to be a presentation title page. ({len(text1)})"
            )
        if len(text2) > MAXLEN:
            text2 = text2[:MAXLEN]
            logger.error(
                f"Text from tesseract ocr is too long to be a presentation title page., ({len(text2)})"
            )

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
        return None


def iterate_dataSet():
    dataset_path = "/uw/invest-data/downloadlinks/data/dataset.csv"
    df = pd.read_csv(dataset_path)
    df = df[df["presentation"] == 3]
    for index, row in df.iterrows():
        print(row)
        # yield the row
        yield row


def create_the_new_tagger():
    for pdf_link in iterate_dataSet():
        pdf_link = "/dave/presentations/" + pdf_link["fname"]
        result = askgpt_mix(pdf_link)
        print(result)


if __name__ == "__main__":
    create_the_new_tagger()
    # iterate_dataSet()
    # result = askgpt_mix("path_to_your_pdf.pdf")
    # print(result)
# Example of how to use this function:
# result = askgpt_mix("path_to_your_pdf.pdf")
