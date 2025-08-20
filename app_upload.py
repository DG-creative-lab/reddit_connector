from flask import Flask, request
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
import praw
from datetime import datetime
import logging

#### initiate the app #####

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="Reddit API",
    description="API for extracting subreddit data",
)

######## set up the configs ##########

# Configuration for SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///subredditv6.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initiate the db - always initiate after the config
db = SQLAlchemy(app)

# Default Reddit API credentials (placeholder values)
app.config["REDDIT_ID"] = "default_client_id"
app.config["REDDIT_SECRET"] = "default_client_secret"
app.config["REDDIT_USER_AGENT"] = "default_user_agent"


# Global variable for Reddit client
reddit = None


def get_reddit():
    global reddit
    if reddit is None:
        reddit = praw.Reddit(
            client_id=app.config["REDDIT_ID"],
            client_secret=app.config["REDDIT_SECRET"],
            user_agent=app.config["REDDIT_USER_AGENT"],
        )
    return reddit


# Custom logging handler to capture PRAW logs
class PRAWLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        db.session.add(PRAWLogData(log=log_entry))
        db.session.commit()


# Configure logging for PRAW within the Flask app context
with app.app_context():
    # Instantiate the custom logging handler
    praw_log_handler = PRAWLogHandler()

    # Configuring PRAW logs
    for logger_name in ("praw", "prawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(praw_log_handler)


################ db Models ######################


# Define the SQLAlchemy model for keyword and account data
class KeywordData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), unique=True, nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


# Define the SQLAlchemy model for subreddit data
class SubredditData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subreddit = db.Column(db.String(21), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    keyword_data_id = db.Column(
        db.Integer, db.ForeignKey("keyword_data.id"), nullable=False
    )


# Database model for PRAW logs
class PRAWLogData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Create tables
with app.app_context():
    db.create_all()

############ API MODELS #############################
# Define the resource model for getting user authentication credentials for reddit

credential_model = api.model(
    "RedditCredentials",
    {
        "client_id": fields.String(required=True, description="The Reddit client ID"),
        "client_secret": fields.String(
            required=True, description="The Reddit client secret"
        ),
        "user_agent": fields.String(required=True, description="The Reddit user agent"),
    },
)

# Define the API model for subreddit data
subreddit_model = api.model(
    "Subreddit",
    {
        "subreddit": fields.String(
            required=True, unique=True, description="The name of the subreddit"
        ),
        "comment": fields.String(required=True, description="The comment"),
        "created_date": fields.DateTime(
            required=True,
            description="The creation date of the post",
            dt_format="iso8601",
        ),
        "author": fields.String(required=True, description="The author of the post"),
        "title": fields.String(required=True, description="The title of the post"),
        "keyword_data_id": fields.Integer(
            required=True, description="ID of the associated keyword"
        ),
    },
)


# Define the API model for keyword and account data
keyword_model = api.model(
    "Keyword",
    {
        "keyword": fields.String(
            required=True,
            description="The keyword (max length: 21, only underscores allowed)",
        ),
        "account_name": fields.String(required=True, description="The account"),
        "industry": fields.String(
            required=True, description="The industry of the account"
        ),
        "timestamp": fields.DateTime(description="Timestamp"),
    },
)


# Model for PRAW logs
praw_log_model = api.model(
    "PRAWLog",
    {
        "id": fields.Integer(description="Log ID"),
        "log": fields.String(description="PRAW Log Message"),
        "timestamp": fields.DateTime(description="Timestamp"),
    },
)


###################### REST API ##################
# REST API endpoint for Reddit authentication credentials

@api.route("/reddit_credentials")
class RedditCredentials(Resource):
    @api.expect(credential_model)
    def post(self):
        global reddit
        credentials = request.json
        app.config["REDDIT_ID"] = credentials["client_id"]
        app.config["REDDIT_SECRET"] = credentials["client_secret"]
        app.config["REDDIT_USER_AGENT"] = credentials["user_agent"]

        # Reset the Reddit client
        reddit = None

        return {"message": "Credentials updated successfully"}, 200


# REST API endpoint for PRAW logs
@api.route("/praw_logs")
class PRAWLogsResource(Resource):
    @api.marshal_list_with(praw_log_model)
    def get(self):
        # Get PRAW logs from the database
        praw_logs = PRAWLogData.query.all()

        print(
            "Number of logs retrieved:", len(praw_logs)
        )  # Add this line for debugging

        return praw_logs


# REST API endpoint for subreddit and keyword


@api.route("/keyword_data")
class KeywordDataResource(Resource):
    @api.expect(
        api.parser().add_argument(
            "keyword", type=str, required=True, help="Keyword to match on subreddits"
        )
    )
    @api.marshal_with(subreddit_model, as_list=True)
    def get(self):
        keyword = request.args.get("keyword")

        if not keyword:
            return {"error": 'Missing or invalid "keyword" parameter'}, 400

        # Check if the keyword is in the keyword database
        existing_keyword_data = KeywordData.query.filter_by(keyword=keyword).first()
        if existing_keyword_data:
            # Check if the keyword is in the subreddit database
            subreddit_data_list = SubredditData.query.filter_by(
                keyword_data_id=existing_keyword_data.id
            ).all()
            if subreddit_data_list:
                # Return subreddit data from the database if available
                return subreddit_data_list

        # If keyword not found in the subreddit database, run API calls to Reddit
        reddit_data_list = []
        for submission in reddit.subreddit(keyword).hot(limit=10):
            # Convert Unix timestamp to datetime
            created_date = datetime.utcfromtimestamp(submission.created_utc)
            reddit_data_list.append(
                {
                    "subreddit": submission.subreddit.display_name,
                    "comment": submission.selftext
                    if submission.selftext
                    else "No comments",
                    "created_date": created_date,
                    "author": submission.author.name
                    if submission.author
                    else "Unknown",
                    "title": submission.title,
                }
            )

        # Record new keyword and subreddit data in the databases
        if not existing_keyword_data:
            # Record keyword, account name, and industry in the keyword database
            account_name = request.args.get("account_name")
            industry = request.args.get("industry")

            if not account_name or not industry:
                return {
                    "error": 'Missing or invalid "account_name" or "industry" parameters. Provide both.'
                }, 400

            new_keyword_data = KeywordData(
                keyword=keyword, account_name=account_name, industry=industry
            )
            db.session.add(new_keyword_data)
            db.session.commit()

        # Record new subreddit data in the subreddit database and relate it to the keyword database
        new_subreddit_data = [
            SubredditData(
                keyword_data_id=existing_keyword_data.id
                if existing_keyword_data
                else new_keyword_data.id,
                subreddit=data["subreddit"],
                comment=data["comment"],
                created_date=data["created_date"],
                author=data["author"],
                title=data["title"],
            )
            for data in reddit_data_list
        ]
        db.session.add_all(new_subreddit_data)
        db.session.commit()

        return new_subreddit_data

    @api.expect(keyword_model)
    @api.marshal_with(keyword_model)
    def post(self):
        data = request.json
        keyword_data = KeywordData(
            keyword=data["keyword"],
            account_name=data.get("account_name"),
            industry=data.get("industry"),
        )
        db.session.add(keyword_data)
        db.session.commit()
        return keyword_data


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create the database tables
    app.run(debug=True)
