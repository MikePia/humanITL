from flask import jsonify
import logging
import os
import pandas as pd

try:
    from .models import persist  # When part of the package
except ImportError:
    from models import persist  # When run as a standalone script


from db_code import fetchLinksForDCAT, update_local_db, reset_unprocessed_links
from clickbuttons import automate_browser_actions

from classify.predict import predict
from tagger import askgpt, askgpt_mix

logger = logging.getLogger(__name__)

download_dir = os.getenv("DOWNLOAD_DIRECTORY")


def register_download(req):
    data = req.json
    download_id = data["downloadId"]
    # url = data["url"]
    # Store download info; consider using a database for production environments
    # persist.store_id(download_id, url)
    return jsonify({"message": "Download registered", "downloadId": download_id}), 200


def process_row(req):
    print("where the fuck is my debugger")
    try:
        data = req.json
        filename, url = data.get("filename"), data.get("url")

        if not filename or not url:
            return jsonify(
                {"success": False, "message": "Missing filename or URL"}
            ), 400

        if not persist.remove_uncertainty(url):
            return jsonify(
                {
                    "success": False,
                    "message": "URL is not recognized. Remove it from the list",
                }
            ), 422

        if persist.is_processed(url):
            return jsonify(
                {"success": False, "message": "Row was already processed previously"}
            ), 409

        process_document(filename, url)
        update_local(url)
 
        return jsonify({"success": True, "message": "Row processed successfully"}), 200
    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Flask failed to process row: {str(e)}"}
        ), 500

def download_decision(req):
    try:
        data = req.json
        downloads = data.get("downloads", [])
        # Assuming 'persist' is a pre-defined object handling your data persistence
        for i, download in enumerate(downloads):
            row = persist.get_url_row(downloads[i]["url"])  # Make sure this method is defined in your PersistDF or equivalent class
            if not row or row['status'] == 'done':
                downloads[i]['action'] = 'delete'
            else:
                downloads[i]['action'] = 'download'  # This should be a string indicating the action to take
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Proper error handling

    return jsonify(downloads)  # This ensures the response is in the expected format



def might_be_pdf(req):
    data = req.json
    print(data)
    url = data["docLink"]
    if not persist.update_classification(url, None, 2):
        return jsonify({"success": True, "message": "Row processed conditionally"})
    persist.set_status(url, "processed")
    persist.set_uncertainty(url)

    return jsonify({"success": True, "message": "Row processed conditionally"})


def tab_opened(req):
    data = req.json
    url = data["url"]
    if not persist.update_classification(url, None, 2) or not persist.set_status(
        url, "processed"
    ):
        return jsonify({"message": "Bad request, URL missing"}), 400
    persist.remove_uncertainty(url)
    return jsonify({"message": f"Successfully processed URL: {url}"}), 200


def handle_html(req):
    data = req.json
    print(data)
    persist.update_classification(data["docLink"], None, 2)
    persist.set_status(data["docLink"], "processed")
    return jsonify({"success": True, "message": "Row processed successfully"})


def start_batch(req):
    data = req.json
    batch_size = data.get("batch_size")
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
    reset_unprocessed_links(unprocessed["id"].to_list())
    persist.reset()
    return jsonify({"success": True})

    # persist.set_processed()
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


def update_local(url=None):
    archive_docs(url)
    persist.set_done(url)


def archive_docs(url=None):
    try:
        if url:
            row_data = persist.get_url_row(url)
            local_archive_these = (
                row_data.to_frame().T
                if isinstance(row_data, pd.Series)
                else pd.DataFrame()
            )
        else:
            local_archive_these = persist.get_processed()

        if local_archive_these.empty:
            return

        for i, row in local_archive_these.iterrows():
            update_local_db(
                row["id"],
                row["pdf_link"],
                row["classify"],
                row["title"],
                row["status"],
                row["sector"],
                row["author"],
                row["date"],
                row["filename_location"],
            )

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
