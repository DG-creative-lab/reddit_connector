
class Config:
    # Configuration for SQLite database
    SQLALCHEMY_DATABASE_URI = "sqlite:///subredditv6.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Default Reddit API credentials (placeholder values)
    REDDIT_ID = "default_client_id"
    REDDIT_SECRET = "default_client_secret"
    REDDIT_USER_AGENT = "default_user_agent"
