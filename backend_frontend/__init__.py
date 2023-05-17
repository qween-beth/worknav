import os
import secrets
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest


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

# Configure mail server
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jasperobed@gmail.com'
app.config['MAIL_PASSWORD'] = 'pwgoiqtmossldcyu'
app.config['MAIL_DEFAULT_SENDER'] = 'WorkcationFinder <noreply@workcationfinder.com>'
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False
mail = Mail(app)

from backend_frontend import routes
