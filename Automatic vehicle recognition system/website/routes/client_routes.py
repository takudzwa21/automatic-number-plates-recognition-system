from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import  current_user, login_required
from ..models import Client, Vehicle, LoginLogout, EntryApproval, Guard  # Notice the relative import
from .. import db , logging
from ..forms import ClientForm, DeleteClientForm
from .admin import superuser_required
import pdfkit
from .other import send_notification_email
import re
from .auth import email_regex, validate_phone_number

client_routes = Blueprint('client_routes', __name__)
 
@client_routes.route('/clients', methods = ["GET", "POST"])
@login_required
def clients():

    """
    Handles displaying a list of clients and potentially processing search results.

    GET:
        1. Retrieves all clients from the 'Client' model using Client.query.all().
        2. Renders the 'clients.html' template, passing the list of clients and
           the current user's data for display and potential actions.

    """
    clients = Client.query.all() 
    logging.info(f"Clients {clients} retrieved successfully by user: {current_user.username} (ID: {current_user.guard_id})")

    return render_template('clients.html', clients=clients, user=current_user)


@client_routes.route("/add_client", methods=["GET","POST"])
@login_required
def add_client():
    """
    Handles the creation of a new client.

    GET:
        1. Creates an instance of the 'ClientForm' class for user input.
        2. Renders the 'add_client.html' template with the form.

    POST:
        1. Validates the submitted form data using the 'validate_on_submit()' method 
           of the 'ClientForm' class.
        2. If the validation is successful:
            * Extracts the form data.
            * Creates a new 'Client' object using the extracted data.
            * Adds the new client object to the database session using 'db.session.add()'.
            * Commits the changes to the database using 'db.session.commit()'.
            * Displays "success" messages using Flask's 'flash' functionality.
            * Redirects the user to the 'add_vehicle' route for the newly created client.
        3. If the validation fails:
            * Displays an "error" message using the 'flash' functionality.
            *  Re-renders the 'add_client.html' template with the form for the user to 
               correct any errors. 
    """
 
    form = ClientForm()

    if request.method == 'POST': 
        if form.validate_on_submit():
            first_name = request.form.get("first_name")  
            last_name = request.form.get("last_name")  
            address = request.form.get("address")  
            phone_number = request.form.get("phone_number")
            email = request.form.get("email")  
            
            new_client = Client(
                first_name=first_name, 
                last_name=last_name, 
                address=address,
                email=email,
                phone_number = phone_number
            )

            if not first_name or not last_name or not email or not address or not phone_number:
                flash("You must enter all details", 'error')
                return render_template("add_client.html", form=ClientForm(obj=new_client), user=current_user)

            
            # Uniqueness Check 
            if Client.query.filter_by(email=email).first():
                flash("A client with this email already exists.", 'error')
                return render_template("add_client.html", form=ClientForm(obj=new_client), user=current_user)

          

              # Validate email format using a regular expression
            if not re.fullmatch(email_regex, email):  
                flash('Invalid email format.', category='error')
                return render_template("add_client.html", form=ClientForm(obj=new_client), user=current_user)

            if not validate_phone_number(phone_number):
                flash("Invalid phone number format [Please enter your phone number in an international format starting with your country code (e.g., +2634455...).]", 'error')
                return render_template("add_client.html", form=ClientForm(obj=new_client), user=current_user)


            try:
                db.session.add(new_client)
                db.session.commit()
                logging.info(f"New client added (ID: {new_client.client_id}) by guard: {current_user.guard_id}")
                try:
                    send_notification_email(
                        recipient_email=new_client.email,
                        subject="Welcome to Our System!",
                        template="client_added.html",
                        client_name=new_client.first_name + " " + new_client.last_name,
                        client_address = new_client.address,
                        client_phone_number = new_client.phone_number,
                        client_email=new_client.email
                    )
                except Exception as e:
                    flash(str(e))
                    
                flash("Client added!", 'success')
                flash("Add vehicle for the client", 'success')
                return redirect(url_for('vehicle_routes.add_vehicle', client_id = new_client.client_id)) # Redirect to a success page
            except Exception as e:
                logging.error(f"Failed to add client: {e}")  # Log database errors
                flash(f"An error occurred: {str(e)}", 'error')
                return render_template("add_client.html", form=ClientForm(obj=new_client), user=current_user)

    return render_template("add_client.html", form=form, user=current_user) 


@client_routes.route('/clients/<client_id>', methods=["GET", "POST"])
@login_required
def client_detail(client_id):
    """
    Handles displaying the details of a specific client and their associated vehicles.

    1. Attempts to retrieve a 'Client' object using the provided 'client_id' 
       and the 'Client.query.filter_by(client_id=client_id).first_or_404()' method. 
       If the client is not found, a 404 error is automatically raised.
    2. Retrieves all vehicles associated with the client using 'client.vehicles', 
       ordered in descending order by their make.
    3. Renders the 'client_detail.html' template, passing the client object, the 
       associated vehicle records, and the current user's data.
    """

    client = Client.query.filter_by(client_id=client_id).first_or_404()
    vehicle_records = client.vehicles.order_by(Vehicle.make.desc()).all()
    logging.info(f"Client details (ID: {client.client_id}) viewed by guard: {current_user.guard_id}")  

    return render_template('client_detail.html', client=client, vehicle_records=vehicle_records, user=current_user)


@client_routes.route("/update_client/<client_id>", methods=["GET", "POST"]) 
@login_required
def update_client(client_id):
    """
    Handles the modification of an existing client's information.

    GET:
       1. Retrieves the Client object with the given 'client_id' from the database.
       2. If the client is not found, displays an "error" message and redirects.
       3. Populates an instance of 'ClientForm' with the existing client data.
       4. Renders the 'update_client.html' template with the form for the user to 
          make changes.

    POST:
       1. Validates the submitted form data using the 'validate_on_submit()' method 
          of the 'ClientForm' class.
       2. If the validation is successful:
          * Updates the Client object's attributes using the 'form.populate_obj()' method.
          * Commits the changes to the database using 'db.session.commit()'.
          * Displays a "success" message using 'flash' functionality.
          * Redirects the user to the updated client's detail page.
       3. If the validation fails:
          * Displays an "error" message using the 'flash' functionality.
          * Re-renders the 'update_client.html' template with the form so that the user 
            can correct any errors (and returns an HTTP 400 Bad Request status code).
    """
    client = Client.query.filter_by(client_id=client_id).first()

    if not client:
        flash("Vehicle not found", 'error')
        return redirect(url_for('home_routes.home'))  # Redirect to appropriate page

    form = ClientForm(obj=client) 

    if request.method == 'POST':  
       
        if form.validate_on_submit():
            if not validate_phone_number(form.phone_number.data):  # Your custom validation
                flash("Invalid phone number format [Please enter your phone number in an international format starting with your country code (e.g., +2634455...).]", 'error')

                return render_template("update_client.html", form=form, client_id=client_id, user=current_user), 400 
            
            # Validate email format using a regular expression
            if not re.fullmatch(email_regex, form.email.data):  
                flash('Invalid email format.', category='error')
                return render_template("update_client.html", form=form, client_id=client_id, user=current_user), 400
            

            # Email uniqueness check  
            existing_client = Client.query.filter(
                            Client.email == form.email.data,
                            Client.client_id != client_id
                        ).first()
            if existing_client and existing_client.client_id != client_id:
                flash("A client with this email already exists.", 'error')
                return render_template("update_client.html", form=form, client_id=client_id, user=current_user), 400
            
            
           

            try:
                form.populate_obj(client)
                db.session.commit()
                logging.info(f"Client updated (ID: {client.client_id}) by guard: {current_user.guard_id}")  # Log Success
                try:
                    send_notification_email(
                        recipient_email=client.email,
                        subject="Account update!",
                        template="client_updated.html",
                        client_name=client.first_name + " " + client.last_name,
                        client_id = client.client_id,
                        client_address = client.address,
                        client_phone_number = client.phone_number,
                        client_email=client.email
                    )
                except Exception as e:
                    flash(str(e))
                flash("Client updated!", 'success')
                return redirect(url_for('client_routes.client_detail', client_id=client_id))  # Redirect to success page
            except Exception as e:
                logging.error(f"Failed to update client (ID: {client.client_id}): {e}") 
                flash("An error occurred while updating the client.", 'error')
                return redirect(url_for('client_routes.client_detail', client_id=client_id))  

                
        else:
            flash("There were errors in the form. Please correct them.", 'error')
            return render_template("update_client.html", form=form, client_id=client_id, user=current_user), 400 

    # GET request
    return render_template("update_client.html", form=form, client_id=client_id, user=current_user) 

@client_routes.route("/delete_client/<client_id>", methods=["GET", "POST"]) 
@login_required
def delete_client(client_id):
    """
    Handles the deletion of a client from the database.

    GET:
        1. Retrieves the Client object with the given 'client_id'.
        2. If the client is not found, displays an "error" message and redirects.
        3. Creates an instance of 'DeleteClientForm' (for confirmation purposes).
        4. Renders the 'delete_client.html' template with the form and the client data.

    POST:
        1. Checks if the HTTP method is 'POST' and if the form's '_method' field is set 
           to 'DELETE'  (this generally indicates confirmation of the deletion action).
        2. If confirmed:
            * Deletes the Client object from the database using 'db.session.delete()'.
            * Commits the changes to the database using 'db.session.commit()'.
            * Displays a "success" message using the 'flash' functionality.
            * Redirects the user to the clients listing page.
        3. If the user cancels or the request is unexpected, redirects to the clients 
           listing page.
    """
    client = Client.query.filter_by(client_id=client_id).first()

    if not client:
        flash("Client not found", 'error')
        return redirect(url_for('client_routes.clients')) 

    if request.method == 'POST':  
        if request.form.get('_method') == 'DELETE': # Check for Delete button
                for vehicle in client.vehicles :
                    db.session.delete(vehicle)
                for loginlogout in  LoginLogout.query.filter_by(client_id=client_id).all():
                    db.session.delete(loginlogout)
                for entryapproval in EntryApproval.query.filter_by(client_id=client_id).all():
                    entryapproval.client_id =  None
                try:
                    db.session.delete(client)
                    db.session.commit()
                    logging.info(f"Client deleted (ID: {client.client_id}) by guard: {current_user.guard_id}")  # Log Success
                    try:
                        send_notification_email(
                            recipient_email=client.email,
                            subject="Account Deletion!",
                            template="client_deleted.html",
                            client_name=client.first_name + " " + client.last_name,
                            client_email=client.email
                        )
                    except Exception as e:
                        flash(str(e))
                    flash("Client deleted!", 'success')
                    return redirect(url_for('client_routes.clients')) 
                except Exception as e:
                    logging.error(f"Failed to delete client (ID: {client.client_id}): {e}") 
                    flash("An error occurred while deleting the client.", 'error')
                    return redirect(url_for('client_routes.clients')) 
        else:  # 'Cancel' or unexpected behavior
                return redirect(url_for('client_routes.clients'))  # Go back home

    form = DeleteClientForm()  
    return render_template("delete_client.html", form=form, client=client, user=current_user)

@client_routes.route('/search_clients') 
def search_clients():
    """
    Handles searching for clients by their first name.

    1. Retrieves the search term from the query string of the URL 
       (e.g., '.../search_clients?first_name=term') using 'request.args.get('first_name')'. 
       Handles an empty search term by assigning an empty string ('') to 'search_term'.

    2. Conditional Query:
       * If 'search_term' is not empty:
           - Queries the 'Client' model to find clients whose first name partially matches 
             the 'search_term' (using case-insensitive 'like' comparison).
           - The '%{search_term}%' pattern allows for finding names that contain the  
             search term anywhere within them. 

       * Else (if 'search_term' is empty):
            - Retrieves all clients from the database.

   3. Renders the 'clients.html' template:
       -  Passes the list of clients (either the filtered results or all clients) to the 
          template for display. 
       -  Includes the current user's data for the template to use.
    """
    search_term = request.args.get('first_name') or ''  # Handle empty search
    
    if search_term:
        clients = Client.query.filter(Client.first_name.like(f'%{search_term}%')).all()
        logging.info(f"Client search performed. Term: {search_term} (by: {current_user.guard_id})")  # Log Search
    else:
        clients = Client.query.all() # Get all clients

    # Re-render the complete page with search results 
    return render_template('clients.html', clients=clients, user=current_user) 



@client_routes.route("/generate_report", methods=["GET"])
@login_required
def generate_report():
    clients = Client.query.all()  # Retrieve all clients from the database
    rendered_template = render_template("report.html", clients=clients)
    pdf = pdfkit.from_string(rendered_template, False)

    return pdf, 200, {'Content-Type': 'application/pdf'}

@client_routes.route('/login_logout_report' )
@login_required
def login_logout_report():
    client_id = request.args.get('client_id')
    # Retrieve filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Query base
    query = (
        db.session.query(LoginLogout, Guard, Client)
    .join(Guard, LoginLogout.guard_id == Guard.guard_id)
    .join(Client, LoginLogout.client_id == Client.client_id) 
    )


    # Apply filters
    if start_date:
        query = query.filter(LoginLogout.login_time >= start_date)
        logging.debug(f"Start date filter applied: {start_date}") 
    if end_date:
        query = query.filter(LoginLogout.login_time <= end_date)
        logging.debug(f"End date filter applied: {end_date}")
    if client_id:
        query = query.filter(LoginLogout.client_id == client_id)
        logging.debug(f"Client ID filter applied: {client_id}") 
    # Fetch entries
    entries = query.all()

    return render_template('reports.html', 
                           entries=entries, 
                           start_date=start_date, 
                           end_date=end_date, 
                           client_id=client_id, user=current_user,
                           )


@client_routes.route('/clear_login_logout_filters')
@login_required
@superuser_required
def clear_login_logout_filters():
    # Construct a base query
    query = LoginLogout.query

    # Retrieve existing filters (if present)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    client_id = request.args.get('client_id')

    # Apply filters to the query
    if start_date:
        query = query.filter(LoginLogout.login_time >= start_date)
        logging.debug(f"Start date filter was present: {start_date}") 
    if end_date:
        query = query.filter(LoginLogout.login_time <= end_date)
        logging.debug(f"End date filter was present: {end_date}") 
    if client_id:
        query = query.filter(LoginLogout.client_id == client_id)
        logging.debug(f"Client ID filter was present: {client_id}")
   
   # Delete relevant entries
    num_deleted = query.delete()  
    db.session.commit()

    logging.info(f"Cleared {num_deleted} login/logout entries (by: {current_user.username})")


    # Redirect back to the report page
    return redirect(url_for('client_routes.login_logout_report', client_id=client_id),) 


 