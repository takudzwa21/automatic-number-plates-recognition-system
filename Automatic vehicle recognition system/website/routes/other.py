from flask import Flask, render_template, Blueprint
from flask_login import login_required, current_user
from flask_mail import Message
from ..import mail, logging

help_routes = Blueprint('help_routes', __name__)  

@help_routes.route('/help')
@login_required
def load_help():
    """Displays the help page (help.html) for logged-in users."""
    logging.info(f"User '{current_user.username}' accessed the help page")
    return render_template('help.html', user=current_user)

settings_routes = Blueprint('settings_routes', __name__)   
@settings_routes.route('/settings')
@login_required
def load_settings():
    """Displays the settings page (settings.html) for logged-in users."""
    logging.info(f"User '{current_user.username}' accessed the settings page")
    return render_template('settings.html', user=current_user)

def send_notification_email(recipient_email, subject, template, **kwargs):
    """Sends a notification email using a rendered template. 

    Args:
        recipient_email (str): The email address of the recipient.
        subject (str): The subject line of the email.
        template (str): The name of the email template file (e.g., 'client_added.html').
        **kwargs: Additional variables to pass to the template.
    """
    message = Message(subject, recipients=[recipient_email])
    message.html = render_template(template, **kwargs)
    mail.send(message)
    logging.info(f"Notification email sent to: {recipient_email}, subject: {subject}")
    


if __name__ == '__main__':
    None