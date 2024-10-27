"""Python Flask API Auth0 integration example
"""

from functools import wraps
import json
from os import environ as env
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from datetime import datetime
from typing import Dict
from six.moves.urllib.request import urlopen
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, jsonify, g, Response, render_template
from flask_cors import cross_origin
from jose import jwt
import requests
import csv
from flask_sqlalchemy import SQLAlchemy
import db_operations

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
API_IDENTIFIER = env.get("API_IDENTIFIER")
SQLALCHEMY_DATABASE_URI = env.get("SQLALCHEMY_DATABASE_URI")
ALGORITHMS = ["RS256"]

app = Flask(__name__, template_folder='templates')
db_path = os.path.join(app.instance_path, 'bizza.db')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    roles = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_superuser = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.username

# Create all database tables
with app.app_context():
    db.create_all()

@app.route('/users')
def get_users():
    users = db_operations.get_all_users()
    return render_template('users.html', users=users)


# Format error response and append status code.
class AuthError(Exception):
    """
    An AuthError is raised whenever the authentication failed.
    """

    def __init__(self, error: Dict[str, str], status_code: int):
        super().__init__()
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex: AuthError) -> Response:
    """
    serializes the given AuthError as json and sets the response status code accordingly.
    :param ex: an auth error
    :return: json serialized ex response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


def get_token_auth_header() -> str:
    """Obtains the access token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description":
                             "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must start with"
                             " Bearer"}, 401)
    if len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                         "description": "Token not found"}, 401)
    if len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must be"
                             " Bearer token"}, 401)

    token = parts[1]
    return token


def requires_scope(required_scope: str) -> bool:
    """Determines if the required scope is present in the access token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False


def requires_auth(func):
    """Determines if the access token is valid
    """

    @wraps(func)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        with urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json") as response:
            jwks = json.loads(response.read())
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.JWTError as jwt_error:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Invalid header. "
                                 "Use an RS256 signed JWT Access Token"}, 401) from jwt_error
        if unverified_header["alg"] == "HS256":
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Invalid header. "
                                 "Use an RS256 signed JWT Access Token"}, 401)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_IDENTIFIER,
                    issuer=f"https://{AUTH0_DOMAIN}/"
                )
            except jwt.ExpiredSignatureError as expired_sign_error:
                raise AuthError({"code": "token_expired",
                                 "description": "token is expired"}, 401) from expired_sign_error
            except jwt.JWTClaimsError as jwt_claims_error:
                raise AuthError({"code": "invalid_claims",
                                 "description":
                                     "incorrect claims,"
                                     " check the audience and issuer"}, 401) from jwt_claims_error
            except Exception as exc:
                raise AuthError({"code": "invalid_header",
                                 "description":
                                     "Unable to parse authentication"
                                     " token."}, 401) from exc

            # Store the payload in Flask's g object instead of _request_ctx_stack
            g.current_user = payload
            return func(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                         "description": "Unable to find appropriate key"}, 401)

    return decorated

@app.route('/')
def index():
    return 'Welcome to Bizza Platform!'


@app.route("/api/v1/venues")
def venues():
    return jsonify({"id":1,"name":"Auditorium A"}), 404


@app.route("/api/v1/speakers")
def speakers():
    firstname = request.args.get("firstname")
    lastname = request.args.get("lastname")
    if firstname is not None and lastname is not None:
        return jsonify(message="The speaker's fullname :" + firstname+" "+ lastname)
    else:
        return jsonify(message="No query parameters in the url")


@app.route("/api/public")
@cross_origin(headers=["Content-Type", "Authorization"])
def public():
    """No access token required to access this route
    """
    response = "Hello from a public endpoint! You don't need to be authenticated to see this."
    return jsonify(message=response)


@app.route("/api/private")
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "http://localhost:3000"])
@requires_auth
def private():
    """A valid access token is required to access this route
    """
    # You can now access the current user from g.current_user
    response = "Hello from a private endpoint! You need to be authenticated to see this."
    return jsonify(message=response)


@app.route("/api/private-scoped")
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "http://localhost:3000"])
@requires_auth
def private_scoped():
    """A valid access token and an appropriate scope are required to access this route
    """
    if requires_scope("read:messages"):
        response = "You need to be authenticated and have a scope of read:messages to see this."
        return jsonify(message=response)
    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)


@app.route("/api/private/profile")
@cross_origin(headers=["Content-Type", "Authorization"])
@cross_origin(headers=["Access-Control-Allow-Origin", "http://localhost:3000"])
@requires_auth
def private_profile():
    """A valid access token is required to access this route
    """
    token = get_token_auth_header()
    headers = {'authorization': f"Bearer {token}"}
    url_items = env.get("API_ENDPOINT")
    response = requests.get(
        url_items,
        headers=headers,
    )
    data = response.json()
    return jsonify(message=data)


@app.errorhandler(404)
# pylint: disable=unused-argument
def page_not_found(error):
    """Page Not Found
    """
    return jsonify({'error': 'Not Found', 'message': 'This page does not exist'}), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=env.get("PORT", 8080))
