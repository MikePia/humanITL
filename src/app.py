import logging
import subprocess
import appconfig  # noqa: F401

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from tagger import askgpt
from db_code import fetchPdfLinksForTagging, update_tags, is_link_classified_and_tagged
import os


logger = logging.getLogger(__name__)

# import appconfig
app = Flask(__name__, static_folder="../static")
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


# @app.route("/update-status", methods=["POST"])
# def update_status_route():
#     link_id = request.form["link_id"]
#     new_status = request.form["status"]

#     conn = pg_connect()
#     cur = conn.cursor()
#     cur.execute(
#         "UPDATE public.pdf_links SET status = %s WHERE id = %s", (new_status, link_id)
#     )
#     conn.commit()
#     cur.close()
#     conn.close()
#     return jsonify({"message": "Status updated successfully"})


@app.route("/start-batch", methods=["POST"])
def start_batch():
    batch_size = request.form.get("batch_size", 10, type=int)
    documents = fetchPdfLinksForTagging(batch_size=batch_size)
    if not documents:
        return jsonify({"error": "No documents found"}), 404
    return jsonify(documents)

@app.route("/process-row", methods=["POST"])
def process_row():
    # Extract filename and URL from the POSTed JSON data
    print('processing row')
    print(request.json)
    data = request.json
    filename = data.get("filename")
    url = data.get("url")

    # Check for the presence of both filename and URL
    if not filename or not url:
        return jsonify({"error": "Missing filename or URL"}), 400

    # Step 1: Handle tagging based on URL or filename content
    tags = perform_tagging(url, filename)
    if not tags:
        return jsonify({"error": "Failed to generate tags, The doc may already be tagged"}), 500
    else:
        success = update_tags(url, "ready", **tags)
        if not success:
            logger.error(f"Failed to update tags for URL {url}")
            # reset status back to ready for all actions on the url
            success = update_tags(url, "ready")
            return jsonify({"success": False, "message": "Failed to update tags"})
        return jsonify({"success": True, "message": "Tags generated successfully"}), 200


def perform_tagging(url, filename) -> dict | None:
    """
    Perform tagging based on URL or filename content. Will refuse to tag docs that are already properly tagged
    """
    if not filename:
        return None

    # Lets not do this if the doc is not classified and without tags openai aint free
    result = is_link_classified_and_tagged(url)
    if result and result["classify"] == 1 and not result["title"]:
        result = askgpt(filename)
        if not result:
            return None
        return result



@app.route("/click-downloads", methods=["POST"])
def click_downloads():
    return jsonify(success=False, message="Not implemented yet")
    data = request.json
    ids = data["ids"]
    url = data["url"]  # Assuming URL is also sent in the POST request
    logging.info(f"Processing {len(ids)} items")

    # Get an absolute path to the Puppeteer script which is here: <fileDir>/../puppeteer/clickButton.js
    fileDir = os.path.dirname(os.path.realpath(__file__))
    puppeteerScriptPath = os.path.abspath(
        os.path.join(fileDir, "..", "puppeteer", "clickButton.js")
    )

    # Call Puppeteer script
    args = ["node", puppeteerScriptPath, url] + ids
    try:
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error("Error in Puppeteer script:", result.stderr)
            return jsonify(
                success=False, message="Failed to process items", error=result.stderr
            )
        logging.info("Successfully processed items")
        return jsonify(success=True, message=f"Processing started for {len(ids)} items")
    except Exception as e:
        logging.error(f"Error triggering downloads: {str(e)}")
        return jsonify(success=False, message=str(e))


def main():
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
