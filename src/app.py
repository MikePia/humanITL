import logging
import appconfig  # noqa: F401

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from tagger import askgpt
from db_code import fetchPdfLinksForTagging, update_tags


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
    data = request.json
    filename = data.get("filename")
    url = data.get("url")

    # Check for the presence of both filename and URL
    if not filename or not url:
        return jsonify({"error": "Missing filename or URL"}), 400

    # Step 1: Handle tagging based on URL or filename content
    tags = perform_tagging(url, filename)
    if not tags:
        return jsonify({"error": "Failed to generate tags"}), 500
    else:
        success = update_tags(url, "ready", **tags)
        if not success:
            logger.error(f"Failed to update tags for URL {url}")
            # reset status back to ready for all actions on the url
            success = update_tags(url, "ready")
            return jsonify({"success": False, "message": "Failed to update tags"})        return jsonify({"success": True, "message": "Tags generated successfully"}), 200


def perform_tagging(url, filename):
    if filename:
        result = askgpt(filename)
        if not result:
            return None
        return result


def main():
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
