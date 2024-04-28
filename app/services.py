import logging
import os
import pandas as pd
from flask import jsonify
from .models import persist
from db_code import fetchLinksForDCAT, batch_update_db, fetchLinksForTestingHtm, fetchLinksForTestingNoExt
from clickbuttons import automate_browser_actions

from classify.predict import predict
from tagger import askgpt, askgpt_mix

logger = logging.getLogger(__name__)

THRESHOLD = 5


def process_row(req):
    print("Processing row")
    data = req.json

    # Validate the input
    filename, url = data.get("filename"), data.get("url")
    if not filename or not url:
        return jsonify({"error": "Missing filename or URL"}), 400

    # Update prediction and tagging
    if persist.is_processed(url):
        return jsonify({"success": False, "message": "Row was already processed previously"}), 200
    process_document(filename, url)

    # Check if the batch size threshold is met for an update
    check_batch_update()

    return jsonify({"success": True, "message": "Row processed successfully"})


def start_batch(req):
    batch_size = req.form.get("batch_size", 3, type=int)
    # documents = fetchLinksForDCAT(batch_size=batch_size)
    # documents = fetchLinksForTestingHtm(batch_size=batch_size)
    documents = fetchLinksForTestingNoExt(batch_size=batch_size)

    if len(documents) == 0:
        return jsonify({"error": "No documents found"}), 404

    # Old unprocessed rows will need to be set to ready
    if persist.df is not None and not persist.df.empty:
        persist.set_processed()

    persist.add_rows(documents)

    returnfmt = persist.df[persist.df['status'] == 'unprocessed'][["id", "pdf_link"]]
    return jsonify(returnfmt.to_dict(orient="records"))


def clear_all(req):
    persist.set_processed()
    check_batch_update()
    return jsonify({"success": True})


def click_downloads(req):
    data = req.json
    batch_size = data.get("batch_size", 5)
    url = os.getenv("FLASK_APP_URL")
    logger.info(f"Processing {batch_size} items")
    ids_called = automate_browser_actions(url, batch_size)
    return jsonify({"ids_called": ids_called})


def process_document(filename, url):
    persist.set_status(url, "processing")
    prediction = int(predict(filename))
    if prediction in [1, 2, 3]:
        persist.update_classification(url, filename, prediction)
        if prediction in [1, 3]:
            handle_tagging(url, filename, prediction)
        persist.set_status(url, "processed")


def handle_tagging(url, filename, prediction):
    tags = perform_tagging(url, filename, prediction)
    if tags:
        persist.update_tags_in_df(url, tags)


def perform_tagging(url, filename, prediction) -> dict:
    if (
        prediction not in [1, 3]
        or persist.df.loc[persist.df["pdf_link"] == url, "title"].values[0]
    ):
        return None
    if prediction == 1:
        return askgpt(filename)  # Example: This function must handle the GPT call
    return askgpt_mix(filename)  # Example: This function must handle the GPT call


def update_tags_in_df(url, tags):
    persist.df.loc[
        persist.df["pdf_link"] == url, ["title", "date", "author", "sector"]
    ] = [tags["title"], tags["date"], tags["author"], tags["sector"]]


def check_batch_update():
    threshold = THRESHOLD  # Set the threshold for batch updates
    if len(persist.df[persist.df["status"] == "processed"]) >= threshold:
        update_database()
        persist.df = pd.DataFrame()  # Reset DataFrame after batch update


def update_database():
    # Filter out processed rows for update
    processed_rows = persist.df[persist.df["status"] == "processed"]
    if not processed_rows.empty:
        batch_update_db(processed_rows)
        print("Database batch update triggered.")
        persist.remove_processed()


if __name__ == "__main__":
    url = "http://127.0.0.1:5500/static/js/html/testPuppeteer.html"

    url = "http://localhost:5000/"
    automate_browser_actions(url, 10)
