from flask_restx import fields

############ API MODELS #############################
# Define the resource model for getting user authentication credentials for reddit

def create_api_models(api):
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

    return {
        "credential_model": credential_model,
        "subreddit_model": subreddit_model,
        "keyword_model": keyword_model,
        "praw_log_model": praw_log_model

    }

