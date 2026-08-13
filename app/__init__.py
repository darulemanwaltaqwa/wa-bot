from flask import Flask, jsonify
from app.config import load_configurations, configure_logging
from .views import webhook_blueprint


def create_app():
    app = Flask(__name__)

    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()

    # Import and register blueprints, if any
    app.register_blueprint(webhook_blueprint)

    # Root endpoint for health checks
    @app.route("/", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "message": "WhatsApp Bot is running"}), 200

    return app
