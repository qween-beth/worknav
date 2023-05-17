import json
import datetime
from time import time
from sqlalchemy import Time
#from itsdangerous import TimedSerializer as Serializer
from flask_login import UserMixin
from flask_marshmallow import Marshmallow
from backend_frontend import db, app, login_manager

ma = Marshmallow(app)

# Initialise a Login_manager object
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User schema
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable = False)
    email = db.Column(db.String(100), unique=True, nullable = False)
    password = db.Column(db.String(100), nullable = False)
    image_file = db.Column(db.String(20), nullable = False, default='default.jpeg')
    date = db.Column(db.DateTime, default=datetime.datetime.now())
    reviews = db.relationship('Review', backref='author', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    # define and set attribute of user class
    def __init__(self, username, email, password, image_file):
        self.username = username
        self.email = email
        self.password = password
        self.image_file = image_file

    # Method to generate token
    def get_reset_token(self, expires_sec=1800):
        #s = Serializer(app.config['SECRET_KEY'], expires_sec)
        user_id_bytes = bytes(str(self.id), 'utf-8')
        print(f'user_id: {self.id}, user_id_bytes: {user_id_bytes}')
        token = json.dumps({'user_id': user_id_bytes.decode('utf-8'), 'exp': time() + expires_sec}).encode('utf-8')
        return token

    @staticmethod
    def verify_reset_token(token):
        #s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = json.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


# Serialization schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','username', 'email', 'password', 'date')


# Workspace schema
class Workspace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workspace_name = db.Column(db.String(100))
    workspace_type = db.Column(db.String(100))
    internet = db.Column(db.String(50)) # stable, fluctuating, disruptive
    electricity = db.Column(db.String(50)) # stable, fluctuating, disruptive
    cost = db.Column(db.Text(200)) # paid, free, negotiable
    opening_time = db.Column(db.Time)
    closing_time = db.Column(db.Time)
    address = db.Column(db.Text(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # define and set attribute of workspace class
    def __init__(self, workspace_name, workspace_type, internet,\
        electricity, cost, opening_time, closing_time, address, latitude, longitude, user_id):
        self.workspace_name = workspace_name
        self.workspace_type = workspace_type
        self.internet = internet
        self.electricity = electricity
        self.cost = cost
        self.opening_time = opening_time
        self.closing_time = closing_time
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.user_id = user_id


# Serialization schema
class WorkspaceSchema(ma.Schema):
    class Meta:
        fields = ('id','workspace_name', 'workspace_type', 'internet', 'electricity',\
             'cost', 'opening_time', 'closing_time','address', 'date')


# Review schema
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_reviewed = db.Column(db.DateTime, default=datetime.datetime.now())
    content = db.Column(db.Text, nullable=False)
    ratings = db.Column(db.Float, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

     # define and set attribute of review class
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


# Book-workspace schema
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workspace_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    booking_time = db.Column(db.Time, nullable=False)
    team_size = db.Column(db.Integer, nullable=False)

     # define and set attribute of booking class
    def __init__(self, workspace_name, username, email, phone, booking_date, booking_time, team_size):
        self.workspace_name = workspace_name
        self.username = username
        self.email = email
        self.phone = phone
        self.booking_date = booking_date
        self.booking_time = booking_time
        self.team_size = team_size

# Serialisation schema
class BookingSchema(ma.Schema):
    class Meta:
        fields = ('id', 'workspace_name', 'username','email', 'phone', 'booking_date', 'booking_time',\
            'team_size')
