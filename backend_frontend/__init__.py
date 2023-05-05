from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
import os
import secrets

# App Configuration
app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(16)

# SQLite configuration (For Development)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workcation_finder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login2'
login_manager.login_message_category = 'info'

from backend_frontend import routes
