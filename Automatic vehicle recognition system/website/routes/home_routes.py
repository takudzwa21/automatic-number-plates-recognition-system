from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import EntryApproval, LoginLogout
from .. import db, logging
from .admin import superuser_required

home_routes = Blueprint('home_routes', __name__)

@home_routes.route('/', methods=['GET', 'POST'])
@login_required
def home():
    """Renders 'system.html'  ."""

    role = request.args.get('role')
    logging.info(f"User '{current_user.username}' accessed the home route")
    if role == 'guard':
        return render_template("system.html", user=current_user)
    if role == 'supervisor':
        return render_template("system.html", user=current_user)
    return render_template("system.html", user=current_user)
 

@home_routes.route('/clear_entry_approvals')
@login_required
@superuser_required
def clear_entry_approvals():
    try:
        num_deleted = LoginLogout.query.delete()  
        db.session.commit()
        logging.info(f"Cleared {num_deleted} entry approvals (by: {current_user.username})")
        flash("Cleared")

    except Exception as e:
        logging.error(f"Failed to clear entry approvals: {e}")
        flash("Failed to clear peak hours." , 'error') 

    return redirect(url_for('home_routes.home'))
    
if __name__ == '__main__':
    None