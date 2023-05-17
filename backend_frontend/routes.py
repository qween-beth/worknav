import os
import datetime
import requests
import sqlite3
import secrets
import googlemaps
from PIL import Image
import mysql.connector
from flask_mail import Message
from flask_login import (LoginManager, login_user, UserMixin,
                        current_user, login_required, logout_user)
from flask import (request, flash, redirect, url_for,
                  render_template, render_template_string,
                  session, get_flashed_messages, abort,
                  jsonify, current_app)
from backend_frontend.forms import (RegistrationForm, LoginForm,
                                    UpdateAccountForm, ReviewForm,
                                    BookingForm, RequestResetForm,
                                    ResetPasswordForm)
from backend_frontend import app, db, mail, bcrypt, login_manager
from backend_frontend.models import User, Workspace, Review, Booking


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
    
     # get the path to the instance folder of the Flask app
    #instance_path = current_app.instance_path

    # join the instance path with the name of the database file
    #db_path = os.path.join(instance_path, 'workcation_finder.db')

    # connect to the database
    conn = sqlite3.connect('instance/workcation_finder.db')
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
    return redirect(url_for('dashboard'))


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


# Booking template
# HTML template for the table message sent to workspace admin
TABLE_TEMPLATE = """
<table>
  <tr>
    <th>Workspace</th>
    <td>{{ booking.workspace_name }}</td>
  </tr>
  <tr>
    <th>Email</th>
    <td>{{ booking.email }}</td>
  </tr>
  <tr>
    <th>Phone</th>
    <td>{{ booking.phone }}</td>
  </tr>
  <tr>
    <th>Date</th>
    <td>{{ booking.booking_date }}</td>
  </tr>
  <tr>
    <th>Time</th>
    <td>{{ booking.booking_time }}</td>
  </tr>
  <tr>
    <th>Team Size</th>
    <td>{{ booking.team_size }}</td>
  </tr>
</table>
"""
# Booking endpoint
@app.route('/book_workspace', methods=['GET', 'POST'])
@login_required
def book_workspace():
    form = BookingForm()
    if form.validate_on_submit():
        booking = Booking(
            workspace_name=form.workspace_name.data,
            username=current_user.username,
            email=form.email.data,
            phone=form.phone.data,
            booking_date=form.booking_date.data,
            booking_time=form.booking_time.data,
            team_size=form.team_size.data
        )
        db.session.add(booking)
        db.session.commit()
        
        # Render the table template with the booking data
        table_html = render_template_string(TABLE_TEMPLATE, booking=booking)
        # Send email to the admin
        message_admin = Message('New Booking Request',
                          recipients=['jasperobed@gmail.com'])
        message_admin.html = f"""
        <h2>New booking request from {current_user.username}:</h2>
        {table_html}
        """
        mail.send(message_admin)

        # Send email to the user
        message_user = Message('Your Booking Request',
                               recipients=[form.email.data])
        message_user.html = f"""
        <h2>Your booking request at {form.workspace_name.data}:</h2>
        {table_html}
        """
        mail.send(message_user)
        
        flash('Workspace booked successfully! Workspace admin will contact you.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('book_workspace.html', title='Book Workspace', form=form)

# --------------------------------------------
## JV additional routes
## Route to add a workspace page
@app.route('/add_workspace')
@login_required
def add_workspace():
    return render_template('add_workspace.html')

## Route to add new workspace data to workspace table in db
@app.route('/submit_workspace', methods=['POST'])
@login_required
def submit_workspace():
    workspace_name = request.form['workspace_name']
    workspace_type = request.form['workspace_type']
    internet = request.form['internet']
    electricity = request.form['electricity']
    cost = request.form['cost']
    opening_time_str = request.form['opening_time']
    opening_time = datetime.datetime.strptime(opening_time_str, '%H:%M').time()
    closing_time_str = request.form['closing_time']
    closing_time = datetime.datetime.strptime(closing_time_str, '%H:%M').time()
    address = request.form['address']

    response = requests.get(f'https://api.geoapify.com/v1/geocode/search?text={address}&apiKey=5964526efb1248479d2af5c09c0711a1')
    if response.status_code == 200:
        result = response.json()
        if result['features']:
            latitude = result['features'][0]['properties']['lat']
            longitude = result['features'][0]['properties']['lon']
        else:
            return 'Address not found', 400
    else:
        return 'Error while processing the address', 500
    user_id = current_user.id # provides id of user who submitted the workspace
    
    workspace = Workspace(workspace_name=workspace_name,
                          workspace_type=workspace_type,
                          internet=internet,
                          electricity=electricity,
                          cost=cost,
                          opening_time=opening_time,
                          closing_time=closing_time,
                          address=address,
                          latitude=latitude,
                          longitude=longitude,
                          user_id=user_id)
    db.session.add(workspace)
    db.session.commit()
    flash('Workspace added successfully!', 'success')
    return redirect(url_for('dashboard'))


## Route to render map
@app.route('/static_map')
@login_required
def static_map():
    return render_template('static_map.html')

## Route to obtain data from db to show pins on map
basedir = os.path.abspath(os.path.dirname(__file__))
@app.route('/data', methods=['POST', 'GET'])
@login_required
def get_data():
     # get the path to the instance folder of the Flask app
    instance_path = current_app.instance_path

    # join the instance path with the name of the database file
    db_path = os.path.join(instance_path, 'workcation_finder.db')

    # connect to the database
    conn = sqlite3.connect(db_path)
    #conn = sqlite3.connect('instance/workcation_finder.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workspace')
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

# Reset email function
def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('reset_token', token=token, _external=True)
    user_msg = Message('Password Reset Request',
                  recipients=[user.email])
    user_msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(user_msg)


# Password request endpoint
@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login2'))
    return render_template('reset_request.html', title='Reset Password', form=form)


# Reset password token endpoint
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login2'))
    return render_template('reset_token.html', title='Reset Password', form=form)
