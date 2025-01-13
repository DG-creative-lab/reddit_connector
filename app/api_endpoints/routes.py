from flask import Blueprint, request, current_app
from flask_restx import Api, Resource, reqparse
from app import api
from app.models.api_models import create_api_models
from app.models.db_models import PRAWLogData
#from app.models.api_models import credential_model, subreddit_model, keyword_model, praw_log_model
from app.services.keyword_services import (
    add_keyword_data,
    get_subreddit_data_by_keyword,
    fetch_and_store_reddit_data
)

api_blueprint = Blueprint('endpoint', __name__)
endpoint = Api(api_blueprint, title='Reddit API', description='API for extracting subreddit data')

api_models = create_api_models(api)

@endpoint.route("/reddit_credentials")
class RedditCredentials(Resource):
    @endpoint.expect(api_models["credential_model"])
    def post(self):
        global reddit
        credentials = request.json
        current_app.config["REDDIT_ID"] = credentials["client_id"]
        current_app.config["REDDIT_SECRET"] = credentials["client_secret"]
        current_app.config["REDDIT_USER_AGENT"] = credentials["user_agent"]

        # Reset the Reddit client
        reddit = None

        return {"message": "Credentials updated successfully"}, 200


# REST API endpoint for PRAW logs
@endpoint.route("/praw_logs")
class PRAWLogsResource(Resource):
    @endpoint.marshal_list_with(api_models["praw_log_model"])
    def get(self):
        # Get PRAW logs from the database
        praw_logs = PRAWLogData.query.all()

        print(
            "Number of logs retrieved:", len(praw_logs)
        )  # Add this line for debugging

        return praw_logs
    

@endpoint.route("/keyword_data")
class KeywordDataResource(Resource):
    @endpoint.expect(reqparse.RequestParser().add_argument("keyword", type=str, required=True, help="Keyword to match on subreddits"))
    @endpoint.marshal_with(api_models["subreddit_model"], as_list=True)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("keyword", type=str, required=True, help="Keyword to match on subreddits")
        args = parser.parse_args()
        keyword = args['keyword']

        subreddit_data_list = get_subreddit_data_by_keyword(keyword)
        if subreddit_data_list is not None:
            return subreddit_data_list

        keyword_data = add_keyword_data(keyword)
        return fetch_and_store_reddit_data(keyword, keyword_data.id)

    @endpoint.expect(api_models["keyword_model"])
    @endpoint.marshal_with(api_models["keyword_model"])
    def post(self):
        data = request.json
        keyword_data = add_keyword_data(data["keyword"], data.get("account_name"), data.get("industry"))
        return keyword_data, 201

