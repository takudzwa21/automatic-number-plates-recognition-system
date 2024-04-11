from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..models import Guard  # Import the 'Guard' user model
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db, logging  # Import the database instance
from flask_login import login_user, login_required, logout_user, current_user, user_logged_out
import re
from .other import send_notification_email
from functools import wraps
auth = Blueprint('auth', __name__)  # Create a blueprint named 'auth'
from flask import g, redirect, url_for


def home_if_logged_in(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if current_user.is_authenticated:  # Check if user is logged in (using g.user)
      return redirect(url_for('home_routes.home'))  # Redirect to home page
    return f(*args, **kwargs)
  return decorated_function


@auth.route('/login', methods=['GET', 'POST'])
@home_if_logged_in
def login():
    """Handles user login for both regular guards and the supervisor."""
 
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
      
        role = request.form.get('role') 

        logging.debug(f"Login attempt with email: {email}, role: {role}")

        if role == 'guard':
            # Find a regular guard (excluding the supervisor) by email
            user = Guard.query.filter(Guard.supervisor != True, Guard.email == email).first()
        else:
            # Assume the supervisor has a guard_id of 1
            user = Guard.query.filter(Guard.supervisor == True, Guard.email == email).first()

        if user:
            # Check if the provided password matches the stored hash
            if check_password_hash(user.password, password): 
               
                if user.suspended:
                
                    flash("You are suspended!")
                    return redirect(url_for("auth.login"))
                
                login_user(user, remember=True)  
                flash('Logged in successfully!', category='success')
                # Redirect based on user role
                if user.supervisor :  # Supervisor
                    logging.info(f"Supervisor (ID: {user.guard_id}) logged in")
                    return redirect(url_for('accounts.view_accounts')) 
                else:  # Regular guard
                    logging.info(f"Guard (ID: {user.guard_id}) logged in")
                    return redirect(url_for('home_routes.home', role=role)) 
            else:
                logging.warning(f"Incorrect password for user: {email}")
                flash('Incorrect password, try again.', category='error')
        else:
            logging.warning(f"Login failed: Email {email} not found")
            flash('Email does not exist for that role.', category='error')
            
            

    # GET request: Render the login template 
    return render_template("login.html", user=current_user, email = None) 


@auth.route('/logout')
@login_required  # Require the user to be logged in for logout
def logout():
    """Handles user logout."""

    logout_user()  
    return redirect(url_for('auth.login'))  # Redirect to the login screen

email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Example email regex
import phonenumbers

def validate_phone_number(phone_number):
  """
  Validates a phone number to ensure international format with only numbers and dashes.

  Args:
      phone_number: The phone number string to validate.

  Returns:
      True if the number is valid in international format with only numbers and dashes, False otherwise.
  """

  try:
    # Use a regular expression to validate format before parsing
    pattern = r"^\+[\d\s\-]+$"  # Starts with +, followed by digits, spaces, or dashes
    if not re.match(pattern, phone_number):
      return False

    # Parse the phone number (assuming international format)
    number = phonenumbers.parse(phone_number, None)  
    # Check if the phone number is possible (more flexible than is_valid_number)
    return phonenumbers.is_possible_number(number)

  except phonenumbers.NumberParseException:
    return False

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    """Handles new user registration."""

    if request.method == 'POST':
        # Retrieve form data
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Check for existing user with the same email
        existing_user = Guard.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists.', category='error')

        # Validate email format using a regular expression
        elif not re.fullmatch(email_regex, email):  
            flash('Invalid email format.', category='error')

        # Validate username (alphanumeric and minimum length)
        elif len(username) < 2 or not username.isalnum(): 
            flash('Username must be greater than 1 character and alphanumeric.', category='error')

        # Check for existing user with the same username 
        elif Guard.query.filter_by(username=username).first():
            flash('Username already exists.', category='error')

        # Check if passwords match
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')

        # Check password length
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')

        # If all validations pass:
        else:
            # Create new user with hashed password 
            new_user = Guard(
                email=email, 
                username=username, 
                password=generate_password_hash(password1, method='scrypt', salt_length=16),
                supervisor = False,
                suspended = False
            )
            db.session.add(new_user)
            db.session.commit()
            try:
                send_notification_email(
                    recipient_email=email,
                    subject="Welcome to Our System!",
                    template="guard_added.html",
                    username=username,
                    email=email,
                )
            except Exception as e:
                flash(str(e))
                
            flash('Account created, Please login using your email and password!')
            return redirect(url_for('auth.login'))

    # GET request: Render the sign-up template
    return render_template("sign_up.html", user=current_user)

if __name__ == '__main__':
    None