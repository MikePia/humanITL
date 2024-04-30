from flask import Flask
from flask_cors import CORS
from .config import Config


def create_app():
    app = Flask(__name__, static_folder="../static")
    app.config.from_object(Config)
    CORS(app)

    from .initroute import init_routes

    init_routes(app)

    return app


# @atexit.register
# def handle_shutdown():
#     print("Shutting down...")
#     if persist.df is not None and not persist.df.empty:
#         update_database()  # Make sure to handle final updates
#         print("Saving data before shutdown...")
