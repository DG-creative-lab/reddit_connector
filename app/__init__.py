from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
#from .models.api_models import create_api_models
from config import Config


# Initialize SQLAlchemy
db = SQLAlchemy()


# Create a function to initialize your Flask app
def create_app(config_class=Config):
    app = Flask(__name__)
    # Load configurations from the 'config.py' file
    app.config.from_object(Config)

    # Initialize Flask-RESTx Api
    api = Api(
        app,
        version="1.0",
        title="Reddit API",
        description="API for extracting subreddit data"
    )

     # Initialize API models
    #create_api_models(api)

    #initialise the database
    db.init_app(app)

    #build the tables
    with app.app_context():
        db.create_all()

    from .api_endpoints.routes import api_blueprint
    app.register_blueprint(api_blueprint)

    return app