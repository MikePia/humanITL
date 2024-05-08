from flask import request, render_template, jsonify
from .services import (
    process_row,
    start_batch,
    clear_all,
    click_downloads,
    handle_html,
    might_be_pdf,
    register_download,
    tab_opened,
    download_decision
)


def init_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/heartbeat")
    def heartbeat():
        return jsonify({"status": "alive"}), 200

    @app.route("/start-batch", methods=["POST"])
    def start_batch_route():
        return start_batch(request)

    @app.route("/process-row", methods=["POST"])
    def process_row_route():
        return process_row(request)

    @app.route("/click-downloads", methods=["POST"])
    def click_downloads_route():
        return click_downloads(request)

    @app.route("/clear-all", methods=["POST"])
    def clear_all_route():
        return clear_all(request)

    @app.route("/handle-html", methods=["POST"])
    def handle_html_route():
        return handle_html(request)

    @app.route("/might-be-pdf", methods=["POST"])
    def might_be_pdf_route():
        return might_be_pdf(request)

    @app.route("/register_download", methods=["POST"])
    def register_download_route():
        return register_download(request)

    @app.route("/tab-opened", methods=["POST"])
    def tab_opened_route():
        return tab_opened(request)
    
    
    @app.route("/download-decision", methods=["POST"])
    def download_decision_route():
        return download_decision(request)
