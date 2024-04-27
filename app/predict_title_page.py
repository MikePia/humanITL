import fitz
import os
from dotenv import load_dotenv


import pandas as pd

import joblib  # For loading the model

from tagtrain.predict_title import extract_features

load_dotenv()



def predict_title_page(pdf_path, model_path, document_id):
    # Load the trained model
    model = joblib.load(model_path)

    features = extract_features(pdf_path, document_id)
    features_df = pd.DataFrame(features)
    
    # scaler = StandardScaler()  # This should be the scaler fitted on the training data
    # features_df[['aspect_ratio', 'word_count', 'image_count']] = scaler.transform(features_df[['aspect_ratio', 'word_count', 'image_count']])

    probabilities = model.predict_proba(features_df.drop(["document_id"], axis=1))[:, 1 ] 

    # Identify the page with the highest probability of being the title page
    title_page_idx = probabilities.argmax()
    title_page_num = features_df.iloc[title_page_idx]["page_num"]

    # return title_page_num, probabilities[title_page_idx], probabilities, features_df
    return title_page_num
