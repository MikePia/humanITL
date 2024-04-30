from datetime import datetime
import logging
import os
import pandas as pd
from flask import jsonify
from threading import Thread, Lock
import pandas as pd

try:
    from .models import persist  # When part of the package
except ImportError:
    from models import persist  # When run as a standalone script


from db_code import fetchLinksForDCAT, batch_update_db, update_local_db, reset_unprocessed_links
from clickbuttons import automate_browser_actions

from classify.predict import predict
from tagger import askgpt, askgpt_mix

logger = logging.getLogger(__name__)

download_dir = os.getenv("DOWNLOAD_DIRECTORY")


def process_row(req):
    try:
        print("Processing row")
        data = req.json

        # Validate the input
        filename, url = data.get("filename"), data.get("url")
        if not filename or not url:
            return jsonify({"error": "Missing filename or URL"}), 400

        persist.remove_uncertainty(url)

        # Update prediction and tagging
        if persist.is_processed(url):
            return jsonify(
                {"success": False, "message": "Row was already processed previously"}
            ), 200
        process_document(filename, url)

        # Check if the batch size threshold is met for an update
        update_local()

        return jsonify({"success": True, "message": "Row processed successfully"})
    except Exception as e:
        logger.error(f"Error processing row: {e}")
        return jsonify({"error": "Flask failed to process row"}), 500


def might_be_pdf(req):
    data = req.json
    print(data)
    persist.update_classification(data["docLink"], None, 2)
    persist.set_status(data["docLink"], "processed")
    persist.set_uncertainty(data["docLink"])
    return jsonify({"success": True, "message": "Row processed conditionally"})


def handle_html(req):
    data = req.json
    print(data)
    persist.update_classification(data["docLink"], None, 2)
    persist.set_status(data["docLink"], "processed")
    return jsonify({"success": True, "message": "Row processed successfully"})


def start_batch(req):
    batch_size = req.form.get("batch_size", 3, type=int)
    clear_all(None)
    documents = fetchLinksForDCAT(batch_size=batch_size)
    # documents = fetchLinksForTestingHtm(batch_size=batch_size)
    # documents = fetchLinksForTestingNoExt(batch_size=batch_size)

    if len(documents) == 0:
        return jsonify({"error": "No documents found"}), 404


    persist.add_rows(documents)

    returnfmt = persist.df[persist.df["status"] == "unprocessed"][["id", "pdf_link"]]
    return jsonify(returnfmt.to_dict(orient="records"))


def clear_all(req):
    """Processes processed rows and clears all unprocessed rows and resests their ready status"""
    update_local()
    unprocessed = persist.get_unprocessed()
    if unprocessed.empty:
        persist.reset()
        return jsonify({"success": True})
    reset_unprocessed_links(unprocessed['id'].to_list())
    persist.reset()
    return jsonify({"success": True})
    
    
    # persist.set_processed()
    # update_local()
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
    if persist.is_tagged(url):
        return None
    if (
        prediction not in [1, 3]
        or persist.df.loc[persist.df["pdf_link"] == url, "title"].values[0]
    ):
        return None
    if prediction == 1:
        return askgpt(filename)  # Example: This function must handle the GPT call
    return askgpt_mix(filename)  # Example: This function must handle the GPT call


def update_local():
    archive_docs()
    persist.set_done()


def archive_docs():
    try:
        local_archive_these = persist.get_processed()
        if local_archive_these.empty:
            return
        for i, row in local_archive_these.iterrows():
            update_local_db(row['id'], row['pdf_link'], row['classify'], row['title'], row['status'], row['sector'], row['author'], row['date'], row['filename_location'])

    except Exception as e:
        print(f"Error uploading files: {e}")
        logger.error(f"Error updating local db: {e}")
        raise


# Example usage of the function
# Assuming persist.df is a pandas DataFrame and is part of a larger persistent data management object or module


if __name__ == "__main__":
    url = "http://127.0.0.1:5500/static/js/html/testPuppeteer.html"

    # url = "http://localhost:5000/"
    automate_browser_actions(url, 10)
    input("Press Enter to continue...")
    # automate_browser_actions(url, 10)
