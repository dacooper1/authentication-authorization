
from flask import Flask, redirect, render_template, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm
from models import db, connect_db, User, Feedback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///aa'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
app.app_context().push()
# db.drop_all()
db.create_all()

app.config['SECRET_KEY'] = "I'LL NEVER TELL!!"

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

# **GET */ :*** Redirect to /register.
@app.route('/')
def home():
    return redirect('/register')

# **GET */register :*** Show a form that when submitted will register/create a user. This form should accept a username, password, email, first_name, and last_name. Make sure you are using WTForms and that your password input hides the characters that the user is typing!
# **POST */register :*** Process the registration form by adding a new user. Then redirect to ***/secret***
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        f_name = form.first_name.data
        l_name = form.last_name.data
        username = form.username.data.lower()
        email = form.email.data
        pwd = form.password.data
        user = User.register(username,pwd)
        user.first_name = f_name
        user.last_name = l_name
        user.email = email

        db.session.add(user)
        db.session.commit()

        session['user']=user.username

        return redirect(f'/users/{user.username}')
    else:
        return render_template('register.html', form=form)

# **GET */login :*** Show a form that when submitted will login a user. This form should accept a username and a password. Make sure you are using WTForms and that your password input hides the characters that the user is typing!
# **POST */login :*** Process the login form, ensuring the user is authenticated and going to ***/secret*** if so.
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.lower()
        pwd = form.password.data
        user = User.authenticate(username, pwd)

        if user:
            session['user'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Incorrect username/password, please try again.']
    return render_template('login.html', form=form)



# **GET */secret :*** Return the text “You made it!” (don’t worry, we’ll get rid of this soon)
@app.route('/secret')
def secret():
    if not session.get('user'):
        flash("Please login to view this page", "warning")
        return redirect('/login')
    return "You made it!"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# GET /users/<username> : Display a template the shows information about that user (everything except for their password). You should ensure that only logged in users can access this page.
# **GET */users/<username> :*** Show information about the given user. Show all of the feedback that the user has given. For each piece of feedback, display with a link to a form to edit the feedback and a button to delete the feedback. Have a link that sends you to a form to add more feedback and a button to delete the user **Make sure that only the user who is logged in can successfully view this page.**

@app.route('/users/<username>')
def user_info(username):
    user = User.query.filter_by(username=username.lower()).first()
    if not user:
        flash(f"User does not exist, please register")
        return redirect('/register')
    elif not session.get('user'): 
        flash(f"Please login to view {user.username}'s profile", "warning")
        session.pop('user', None)
        return redirect('/login')
    else:
        form = DeleteForm()
        return render_template('/user_info.html', user=user, form=form)
    
# **POST *'/users/<username>/delete' :*** Remove the user from the database and make sure to also delete all of their feedback. Clear any user information in the session and redirect to ***/***. **Make sure that only the user who is logged in can successfully delete their account.**
@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f"User does not exist, please register")
        return redirect('/register')
    elif not session.get('user') or session['user'] != user.username:
        flash(f"Please login to delete your profile", "warning")
        session.pop('user', None)
        return redirect('/login')
    else:
        db.session.delete(user)
        db.session.commit()
        session.pop('user', None)
    return redirect('/')

# **GET */users/<username>/feedback/add :*** Display a form to add feedback  **Make sure that only the user who is logged in can see this form.**
# **POST */users/<username>/feedback/add :*** Add a new piece of feedback and redirect to /users/<username> — **Make sure that only the user who is logged in can successfully add feedback.**

@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    form = FeedbackForm()
    user = User.query.filter_by(username=username).first()

    if not session.get('user'):
        flash("Please login to submit feedback", "warning")
        session.pop('user', None)
        return redirect('/login')

    else:
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            feedback = Feedback(title=title, content=content, username=user.username)

            db.session.add(feedback)
            db.session.commit()

            return redirect(f"/users/{user.username}")
        
        else:
            return render_template('add_feedback.html', form=form, user=username)


# **GET */feedback/<feedback-id>/update :*** Display a form to edit feedback — [**](https://curric.springboard.com/software-engineering-career-track/default/exercises/flask-feedback/index.html#id1)Make sure that only the user who has written that feedback can see this form **

# **POST */feedback/<feedback-id>/update :*** Update a specific piece of feedback and redirect to /users/<username> — **Make sure that only the user who has written that feedback can update it.**
        
@app.route('/feedback/<int:feedback_id>/update', methods=["GET", "POST"])
def update_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    form = FeedbackForm(obj=feedback)
    

    if not session['user'] or feedback.username != session['user']:
        flash("Please login to update your feedback")
        session.pop('user', None)
        return redirect('/login')

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("edit_feedback.html", form=form, feedback=feedback)

# **POST */feedback/<feedback-id>/delete :*** Delete a specific piece of feedback and redirect to /users/<username> — **Make sure that only the user who has written that feedback can delete it.**

@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)
    if not session.get('user') or feedback.username != session['user']:
        flash("Please login to delete your feedback")
        session.pop('user', None)
        return redirect('/login')

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")