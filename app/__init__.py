from flask import Flask
from .web import web_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(web_bp)
    return app
