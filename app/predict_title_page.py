import fitz
import os
from dotenv import load_dotenv

import subprocess


import pandas as pd

import joblib  # For loading the model

from tagtrain.predict_title import extract_features

load_dotenv()


def predict_title_page(pdf_path, model_path, document_id):
    """Returns the top 3 possibilities"""
    # Load the trained model
    model = joblib.load(model_path)

    features = extract_features(pdf_path, document_id)
    features_df = pd.DataFrame(features)

    # scaler = StandardScaler()  # This should be the scaler fitted on the training data
    # features_df[['aspect_ratio', 'word_count', 'image_count']] = scaler.transform(features_df[['aspect_ratio', 'word_count', 'image_count']])

    probabilities = model.predict_proba(features_df.drop(["document_id"], axis=1))[:, 1]
    # Get the highest 3 probablilities
    top_3 = probabilities.argsort()[-3:][::-1]
    top_probs = [int(features_df.iloc[x]["page_num"]) for x in top_3]

    return top_probs

    # Identify the page with the highest probability of being the title page
    # title_page_idx = probabilities.argmax()
    # title_page_num = features_df.iloc[title_page_idx]["page_num"]

    # # return title_page_num, probabilities[title_page_idx], probabilities, features_df
    # return title_page_num


def load_document(file_path):
    """Open a PDF file with the system's default viewer."""
    try:
        # Open PDF with default application
        subprocess.run(["xdg-open", file_path], check=True)
        print(f"Document opened: {file_path}")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"Failed to open file {file_path}: {str(e)}")


if __name__ == "__main__":
    fnames = [
        "/dave/tmp2/0000950123-08-011041.pdf",
        "/dave/tmp2/0000950123-09-036315.pdf",
        "/dave/tmp2/0000950134-06-015195.pdf",
        "/dave/tmp2/0001104659-07-011437.pdf",
        "/dave/tmp2/0001193125-17-229756.pdf",
        "/dave/tmp2/0001193125-18-211444.pdf",
        "/dave/tmp2/0001213900-18-012032.pdf",
    ]
    for fname in fnames:
        # open each page with the osloa
        load_document(fname)
        result = predict_title_page(fname, os.getenv("TAGGER_MODEL"), fname)
        print(result)

        # print(predict_title_page(fname, os.getenv("MODEL_PATH"), fname))
