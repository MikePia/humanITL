import logging
import appconfig  # noqa: F401
import os
import pandas as pd
import atexit

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from tagger import askgpt, askgpt_mix
from clickbuttons import automate_browser_actions
from db_code import fetchLinksForDCAT, batch_update_db
from classify.predict import predict


logger = logging.getLogger(__name__)

# import appconfig
app = Flask(__name__, static_folder="../static")
CORS(app)

THRESHOLD = 5
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start-batch", methods=["POST"])
def start_batch():
    batch_size = request.form.get("batch_size", 3, type=int)
    documents = fetchLinksForDCAT(batch_size=batch_size)

    if len(documents) == 0:
        return jsonify({"error": "No documents found"}), 404

    # Remove unprocessed rows before adding new batch
    if persist.df is not None and not persist.df.empty:
        persist.df = persist.df[persist.df["status"] != "unprocessed"]

    persist.add_rows(documents)

    returnfmt = persist.df[["id", "pdf_link"]]
    return jsonify(returnfmt.to_dict(orient="records"))


@app.route("/process-row", methods=["POST"])
def process_row():
    print("Processing row")
    data = request.json

    # Validate the input
    filename, url = data.get("filename"), data.get("url")
    if not filename or not url:
        return jsonify({"error": "Missing filename or URL"}), 400

    # Update prediction and tagging
    process_document(filename, url)

    # Check if the batch size threshold is met for an update
    check_batch_update()

    return jsonify({"success": True, "message": "Row processed successfully"})


def process_document(filename, url):
    persist.df.loc[persist.df["pdf_link"] == url, "status"] = "processing"
    prediction = predict(filename)
    if prediction in [1, 2, 3]:
        update_classification(url, filename, prediction)
        persist.df.loc[persist.df["pdf_link"] == url, "status"] = (
            "processed"  # Update to processed after completion
        )
        if prediction in [1, 3]:
            handle_tagging(url, filename, prediction)


def update_classification(url, filename, prediction):
    persist.df.loc[persist.df["pdf_link"] == url, "classify"] = prediction
    
    # We only want to archive Investor Presentations
    if prediction in [1, 3]:
        persist.df.loc[persist.df["pdf_link"] == url, "filename_location"] = filename


def handle_tagging(url, filename, prediction):
    tags = perform_tagging(url, filename, prediction)
    if tags:
        update_tags_in_df(url, tags)


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
    if len(persist.df[persist.df['status'] == 'processed']) >= threshold:
        update_database()
        persist.df = pd.DataFrame()  # Reset DataFrame after batch update


def update_database():
    # Filter out processed rows for update
    processed_rows = persist.df[persist.df["status"] == "processed"]
    if not processed_rows.empty:
        batch_update_db(processed_rows)
        print("Database batch update triggered.")
        # Insert logic to perform batch update goes here...

        # Remove processed rows from DataFrame
        persist.df = persist.df[persist.df["status"] != "processed"]


@app.route("/click-downloads", methods=["POST"])
def click_downloads():
    data = request.json
    batch_size = data.get("batch_size", 5)
    url = os.getenv("FLASK_APP_URL")
    logging.info(f"Processing {batch_size} items")
    ids_called = automate_browser_actions(url, batch_size)
    return jsonify({"ids_called": ids_called})


@app.route("/clear-all", methods=["POST"])
def clear_all():
    persist.df = pd.DataFrame()
    return jsonify({"success": True})


def main():
    app.run(debug=True, host="0.0.0.0", port=5000)


class persistDF:
    df = None

    def add_rows(self, new_df):
        new_df["status"] = "unprocessed"  # Initialize all new rows as unprocessed
        if self.df is None:
            self.df = new_df
        else:
            self.df = pd.concat([self.df, new_df], ignore_index=True)


@atexit.register
def handle_shutdown():
    print("Shutting down...")
    if persist.df is not None and not persist.df.empty:
        update_database()  # Make sure to handle final updates
        print("Saving data before shutdown...")


persist = persistDF()


if __name__ == "__main__":
    main()
