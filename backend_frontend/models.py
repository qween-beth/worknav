from backend_frontend import db, app, login_manager
import datetime
from flask_login import UserMixin
from sqlalchemy import Time
from flask_marshmallow import Marshmallow

ma = Marshmallow(app)

# Initialise a Login_manager object
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Users table model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable = False)
    email = db.Column(db.String(100), unique=True, nullable = False)
    password = db.Column(db.String(100), nullable = False)
    image_file = db.Column(db.String(20), nullable = False, default='default.jpeg')
    date = db.Column(db.DateTime, default=datetime.datetime.now())
    reviews = db.relationship('Review', backref='author', lazy=True)


    def __init__(self, username, email, password, image_file):
        self.username = username
        self.email = email
        self.password = password
        self.image_file = image_file


# Serialization schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','username', 'email', 'password', 'date')


# Workspace table model
class Workspace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workspace_name = db.Column(db.String(100))
    workspace_type = db.Column(db.String(100))
    internet = db.Column(db.String(50)) #stable, flunctuating, disruptive
    electricity = db.Column(db.String(50)) #stable, flunctuating, disruptive
    cost = db.Column(db.Text(200)) # paid, free, negotiable
    opening_time = db.Column(db.Time)
    closing_time = db.Column(db.Time)
    address = db.Column(db.Text(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, workspace_name, workspace_type, internet,\
        electricity, cost, opening_time, closing_time, address, user_id):
        self.workspace_name = workspace_name
        self.workspace_type = workspace_type
        self.internet = internet
        self.electricity = electricity
        self.cost = cost
        self.opening_time = opening_time
        self.closing_time = closing_time
        self.address = address
        self.user_id = user_id


# Serialization schema
class WorkspaceSchema(ma.Schema):
    class Meta:
        fields = ('id','workspace_name', 'workspace_type', 'internet', 'electricity',\
             'cost', 'opening_time', 'closing_time','address', 'date')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_reviewed = db.Column(db.DateTime, default=datetime.datetime.now())
    content = db.Column(db.Text, nullable=False)
    ratings = db.Column(db.Float, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    

    def __init__(self, title, content, user_id, ratings):
        self.title = title
        self.content = content
        self.user_id = user_id
        self.ratings = ratings

    @property
    def username(self):
        return self.author.username

# Serialization schema
class ReviewSchema(ma.Schema):
    class Meta:
        fields = ('id','title', 'date_reviewed', 'content', 'user_id','ratings')
