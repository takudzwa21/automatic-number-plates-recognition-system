from flask import Blueprint, render_template, flash, redirect, url_for, abort , Response
from flask_login import login_required, current_user 
from functools import wraps
from ..models import Guard, EntryApproval
from .. import db, app , logging
from.other import send_notification_email
import time
from flask_login import LoginManager, login_required
from flask import g, redirect, url_for

login_manager = LoginManager()

 

@login_manager.unauthorized_handler
def unauthorized():
    # Redirect to login page or return an error message
    return redirect(url_for('auth.login')) 

def superuser_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated: 
            return login_manager.unauthorized()  # Handle unauthorized access
        if not current_user.supervisor:
            abort(403)  # Forbidden for non-superusers
        return func(*args, **kwargs)
    return decorated_view

accounts = Blueprint('accounts', __name__)



@app.route('/logs')
@superuser_required
def logs():
    logging.info(f"Superuser {current_user.username} accessed the logs page")  # INFO
    return render_template("log_viewer.html", user=current_user)

LOG_FILE = 'trial.log'  # Rep
@app.route('/log_stream')
def log_stream():
    def generate_log_stream():
        with open(LOG_FILE, 'r') as f:
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line}\n\n"  # Format for Server-Sent Events
                else:
                    time.sleep(0.5)  # Adjust the interval as needed

    return Response(generate_log_stream(), mimetype='text/event-stream')
 

@accounts.route('/accounts')
@login_required  # Require login for accessing this page
@superuser_required # Require superuser
def view_accounts():
    """Displays a list of Guard accounts (excluding the primary admin)."""
 

    # Fetch accounts excluding the primary admin to prevent accidental self-deletion
    accounts = Guard.query.filter().all()

    # Pass the fetched accounts and current_user object to the template for rendering
    return render_template('accounts.html', accounts=accounts, user=current_user)

@accounts.route('/accounts/delete/<int:guard_id>')
@login_required
@superuser_required
def delete_account(guard_id):
    """Deletes a Guard account."""

    # Retrieve the account to be deleted or raise a 404 error if not found
    account = Guard.query.get_or_404(guard_id)

    for entry_log in account.entry_logs:
        entry_log.guard_id = None

    for entry_log in EntryApproval.query.filter_by(guard_id=guard_id).all() :
        entry_log.guard_id = None


 
    try:
        # Delete the account from the database
        db.session.delete(account)
        db.session.commit()
    except  Exception as e:
        flash("An error has occured, Try again")
        return redirect(url_for('accounts.view_accounts'))  # Redirect back to accounts list

    try:
        send_notification_email(
            recipient_email=account.email,  # Adjust the recipient
            subject="Guard Account Deleted",
            template="guard_deleted.html",
            username=account.username,
            email=account.email
        )
    except Exception as e:
        flash(" Error sending email")

    flash('Account deleted.', 'success')
    return redirect(url_for('accounts.view_accounts'))  # Redirect back to accounts list

@accounts.route('/admin/toggle_superuser/<int:guard_id>')
@login_required
@superuser_required
def toggle_superuser(guard_id):
    if not current_user.supervisor:
        return redirect(url_for('home_routes.home'))

    if guard_id == 1:  # Check if the user has ID 1
        flash('You cannot change the status of that user.', 'warning')
        return redirect(url_for('accounts.view_accounts')) 

    user = Guard.query.get_or_404(guard_id)

    # Prevent changing logged-in superuser's own status
    if user == current_user:
        flash('You cannot change your own superuser status.', 'warning')
        return redirect(url_for('accounts.view_accounts')) 

    user.supervisor = not user.supervisor
    
    try:
        db.session.commit()
        flash('Supervisor status updated!', 'success')
        return redirect(url_for('accounts.view_accounts')) 
    except:
        flash('Error updating supervisor status.', 'danger')
        return redirect(url_for('accounts.view_accounts')) 

@accounts.route('/admin/toggle_suspended/<int:guard_id>')
@login_required
@superuser_required
def toggle_suspended(guard_id):
   
    if guard_id == 1:  # Check if the user has ID 1
        flash('You cannot change the status of that user.', 'warning')
        return redirect(url_for('accounts.view_accounts')) 

    user = Guard.query.get_or_404(guard_id)

    # Prevent changing logged-in superuser's own status
    if user == current_user:
        flash('You cannot change your own suspended status.', 'warning')
        return redirect(url_for('accounts.view_accounts')) 

    user.suspended = not user.suspended
    
    try:
        db.session.commit()
        flash('suspended status updated!', 'success')
        return redirect(url_for('accounts.view_accounts')) 
    except:
        flash('Error updating suspended status.', 'danger')
        return redirect(url_for('accounts.view_accounts')) 



if __name__ == '__main__':
    None