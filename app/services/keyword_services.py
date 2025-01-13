from datetime import datetime
from app import db
from app.models.db_models import KeywordData, SubredditData
from app.utils import get_reddit

# this layer handles interactions with the database, encapsulating the logic 
# for adding and fetching KeywordData and SubredditData.


def add_keyword_data(keyword, account_name=None, industry=None):
    keyword_data = KeywordData(keyword=keyword, account_name=account_name, industry=industry)
    db.session.add(keyword_data)
    db.session.commit()
    return keyword_data


def get_subreddit_data_by_keyword(keyword):
    keyword_data = KeywordData.query.filter_by(keyword=keyword).first()
    if keyword_data:
        return SubredditData.query.filter_by(keyword_data_id=keyword_data.id).all()
    return None


def fetch_and_store_reddit_data(keyword, keyword_data_id):
    reddit = get_reddit()
    subreddit_data_list = []
    for submission in reddit.subreddit(keyword).hot(limit=10):
        subreddit_data = SubredditData(
            subreddit=submission.subreddit.display_name,
            comment=submission.selftext or "No comments",
            created_date=datetime.utcfromtimestamp(submission.created_utc),
            author=submission.author.name if submission.author else "Unknown",
            title=submission.title,
            keyword_data_id=keyword_data_id
        )
        subreddit_data_list.append(subreddit_data)
    db.session.add_all(subreddit_data_list)
    db.session.commit()
    return subreddit_data_list
