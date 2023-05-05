import os
import sqlite3
import secrets
import matplotlib.pyplot as plt
import io
import pybase64
from PIL import Image
from flask import request, flash, redirect, url_for,\
    render_template, session, get_flashed_messages, abort
from backend_frontend.forms import RegistrationForm, LoginForm,\
    UpdateAccountForm, ReviewForm
from backend_frontend.models import User, Workspace, Review
from flask_login import LoginManager, login_user, UserMixin,\
    current_user, login_required, logout_user
from backend_frontend import app, db, bcrypt, login_manager
import mysql.connector
import googlemaps


# Google Maps API key
google_maps_api_key = "AIzaSyBk3Y_NesWkyJjCM9it8rkZOQs0IaFnmRU"
# Initialize the Google Maps client
gmaps = googlemaps.Client(key=google_maps_api_key)


# Index endpoint
@app.route("/")
def index():
    return render_template("index.html")


# About Us endpoint
@app.route("/about")
def about():
    return render_template('about.html', title='About')


# Registration endpoint
@app.route('/register2', methods=['GET', 'POST'])
def register2():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, image_file='default.jpg')
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! Log in to continue.', 'success')
        return redirect(url_for('login2'))
    return render_template('register2.html', title='Registration', form=form)


# Login endpoint
@app.route('/login2', methods=['GET', 'POST'])
def login2():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login2.html', title='Login', form=form)
    

# Dashboard endpoint
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title='Dashboard')


# User's profile account endpoint
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


# Logout endpoint
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# delete account endpoint
@app.route("/delete_account", methods=['POST'])
@login_required
def delete_account():
    if not current_user:
        flash("Incorrect password. Please try again.", "danger")
        return redirect(url_for("login2"))
    # delete the user's associated reviews
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    for review in reviews:
        db.session.delete(review)
    # delete the user's account
    db.session.delete(current_user)
    db.session.commit()
    flash("We're sorry to see you go. Your account has been deleted.", "danger")
    # logout the user after deleting their account
    logout_user()
    return redirect(url_for("login2"))


# Google map endpoint
@app.route('/search_results', methods=['GET'])
def search_results():
    location = request.args.get('location')
    workspace_type = request.args.get('workspace_type')
    budget = request.args.get('budget')
    # Search the database for addresses matching the user's search query
    results = search_database(location, workspace_type, budget)
    matching_addresses = search_database(location, workspace_type, budget)
    # Use the Google Maps Geocoding API to convert each address to latitude and longitude
    coordinates = []
    for address in matching_addresses:
        geocode_result = gmaps.geocode(address[8])
        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']
        coordinates.append((latitude, longitude, address))
    # Render the template with the list of latitudes and longitudes
    return render_template('search.html', results=results, coordinates=coordinates)


# search endpoint
@app.route("/search", methods=['GET'])
def search():
    return render_template('search.html')


def search_database(location, workspace_type, budget):
    if location is None:
        return []
    # connect to the database
    conn = sqlite3.connect('workcation_finder.db')
    # create a cursor object
    c = conn.cursor()
    if budget == 'free':
        if workspace_type == 'all':
            c.execute("SELECT * FROM workspace WHERE address LIKE ? AND cost = 'free'", ('%' + location + '%',))
        else:
            c.execute("SELECT * FROM workspace WHERE address LIKE ? AND workspace_type = ? AND cost = 'free'", ('%' + location + '%', workspace_type))
    elif budget == 'paid':
        if workspace_type == 'all':
            c.execute("SELECT * FROM workspace WHERE address LIKE ? AND cost = 'paid'", ('%' + location + '%',))
        else:
            c.execute("SELECT * FROM workspace WHERE address LIKE ? AND workspace_type = ? AND cost = 'paid'", ('%' + location + '%', workspace_type))
    else:
        if workspace_type == 'all':
            c.execute("SELECT * FROM workspace WHERE address LIKE ?", ('%' + location + '%',))
        else:
            c.execute("SELECT * FROM workspace WHERE address LIKE ? AND workspace_type = ?", ('%' + location + '%', workspace_type))

    results = c.fetchall()
    conn.close()
    return results


# create review endpoint
@app.route("/review/new", methods=['GET', 'POST'])
@login_required
def new_review():
    form = ReviewForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        ratings = form.ratings.data
        user_id = current_user.id
        review = Review(title=title, content=content, ratings=ratings, user_id=user_id)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been created!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_review.html', title='New Review',
                           form=form, legend='Share your Workspace experience with others!')





@app.route("/review/<int:review_id>")
def review(review_id):
    review = Review.query.get_or_404(review_id)
    return render_template('review.html', title=review.title, review=review)


# see users' review endpoint
@app.route("/see_reviews")
def see_reviews():
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.order_by(Review.date_reviewed.desc()).paginate(page=page, per_page=5)
    return render_template("see_reviews.html", reviews=reviews)


# update user's review endpoint
@app.route("/review/<int:review_id>/update", methods=['GET', 'POST'])
@login_required
def update_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.author != current_user:
        abort(403)
    form = ReviewForm()
    if form.validate_on_submit():
        review.title = form.title.data
        review.content = form.content.data
        review.ratings = form.ratings.data
        db.session.commit()
        flash('Your review has been updated!', 'success')
        return redirect(url_for('review', review_id=review.id))
    elif request.method == 'GET':
        form.title.data = review.title
        form.content.data = review.content
    return render_template('create_review.html', title='Update Review',
                           form=form, legend='Update Review')


# delete user's review endpoint
@app.route("/review/<int:review_id>/delete", methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.author != current_user:
        abort(403)
    db.session.delete(review)
    db.session.commit()
    flash('Your review has been deleted!', 'success')
    return redirect(url_for('home'))


# user's total review endpoint
@app.route("/user/<string:username>")
def user_reviews(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    reviews = Review.query.filter_by(author=user)\
        .order_by(Review.date_reviewed.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_reviews.html', reviews=reviews, user=user)


# function to save user's profile picture
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    # format to a constant size
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


# Define the route that displays the dashboard
#@app.route('/analytics')
#def analytics():
    # Query the SQLite database to fetch the required data for the analytics
    # You can use SQLAlchemy or the built-in Python sqlite3 library
    # Here's an example using sqlite3
    




















    










