import praw
import logging
from flask import current_app
from app.models.db_models import PRAWLogData
from app import db

# Global variable for Reddit client
reddit = None


def get_reddit():
    global reddit
    if reddit is None:
        reddit = praw.Reddit(
            client_id=current_app.config["REDDIT_ID"],
            client_secret=current_app.config["REDDIT_SECRET"],
            user_agent=current_app.config["REDDIT_USER_AGENT"],
        )
    return reddit


class PRAWLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        db.session.add(PRAWLogData(log=log_entry))
        db.session.commit()


def configure_praw_logging():
    praw_log_handler = PRAWLogHandler()
    for logger_name in ("praw", "prawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(praw_log_handler)
