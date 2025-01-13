from app import db
from datetime import datetime


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