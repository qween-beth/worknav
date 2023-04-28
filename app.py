from flask import Flask, flash, render_template, request, redirect, url_for, jsonify
import secrets
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from models import db, Space, User

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///space.db'

app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


db.init_app(app)


# Create the login manager instance
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()
    space1 = Space.query.filter_by(name='Venture type Claremont').first()
    if not space1:
        space1 = Space(name='Venture type Claremont', type='CoWorkspace', country='Capetwown, South Africa', cost=200, facilities='constant power, ', image='gatsby.jpg')
    space2 = Space.query.filter_by(name='Box-Office').first()
    if not space2:
        space2 = Space(name='Box-Office', type='library', country='Durban, South Africa', cost=500, facilities='power, data', image='mockingbird.jpg')
    space3 = Space.query.filter_by(name='Cross River State Library').first()
    if not space3:
        space3 = Space(name='Cross River State Library', type='library', country='NigeriaAbuja, Nigeria', cost=1200, facilities='power, data', image='pride.jpg')
    space4 = Space.query.filter_by(name='Chill Cafe').first()
    if not space4:
        space4 = Space(name='Chill Cafe', type='cafe', country='Lagos, Nigeria', cost=1949, facilities='power, data', image='1984.jpg')
    db.session.add_all([space1, space2, space3, space4])
    db.session.commit()

    user1 = User.query.filter_by(username='john').first()
    if not user1:
        user1 = User(username='john', email='inspiriasoftware@gmail.com', password_hash='pbkdf2:sha256:260000$pNkaSFv1bpUWxPyX$8925d053609d437afe8410e35f46dd83dfa9c5083bfc45f79da3564b22315cd0')
    user2 = User.query.filter_by(username='jane').first()
    if not user2:
        user2 = User(username='jane', email='petrous7@gmail.com', password_hash='pbkdf2:sha256:260000$LnmN7mrWZpgIufiS$1f0ddbaac0f1d0a7a7ec83c6ec4cbd37362e95dead8bcbe67b45f9035b5408fb')
    db.session.add_all([user1, user2])
    db.session.commit()



class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/add-space', methods=['GET', 'POST'])
def add_space():
    if request.method == 'POST':
        # get form data
        name = request.form['name']
        type = request.form['type']
        country = request.form['country']
        cost = request.form['cost']
        facilities = request.form['facilities']
        # check if image uploaded
        if 'picture' in request.files:
            file = request.files['picture']
            if file and allowed_file(file.filename):
                # secure filename to prevent path traversal attacks
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = 'no_image.jpg'
        else:
            filename = 'no_image.jpg'
        # add space to database
        space = Space(name=name, type=type, country=country, cost=cost, facilities=facilities, image=filename)
        db.session.add(space)
        db.session.commit()
        message = 'space added successfully!'
        flash(message, 'success')
        return redirect('/')
    else:
        return render_template('form.html')


@app.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        results = Space.query.filter(
            (Space.name.like('%{}%'.format(search_query))) |
            (Space.type.like('%{}%'.format(search_query))) |
            (Space.country.like('%{}%'.format(search_query))) |
            (Space.cost.like('%{}%'.format(search_query))) |
            (Space.facilities.like('%{}%'.format(search_query)))
        ).all()
    else:
        results = []
    return render_template('home.html', company_name="WorkNav", results=results)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You have successfully registered!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return render_template('index.html')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash('You have been logged in successfully!', 'success')
        return render_template('index.html')
    return render_template('login.html', title='Log In', form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/index')
def hello():
    name = 'Welcome'
    return render_template('index.html', name=name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

