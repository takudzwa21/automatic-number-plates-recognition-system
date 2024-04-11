from flask import Blueprint, render_template, request, flash,redirect, url_for
from flask_login import current_user, login_required
from ..models import Client, Vehicle
from .. import db
from ..forms import VehicleForm, DeleteVehicleForm
from .other import send_notification_email

vehicle_routes = Blueprint('vehicle_routes', __name__)

@vehicle_routes.route("/add_vehicle/<client_id>", methods=["GET","POST"])
@login_required
def add_vehicle(client_id):
    """
    Handles the creation of a new vehicle associated with a specific client.

    GET Request:
        1. Retrieves the Client object from the database using the provided 'client_id'.
           If the client is not found, an error message is displayed, and the user is 
           redirected to an appropriate page (e.g., the client listing page).
        2. Creates an instance of the 'VehicleForm' class for collecting user input.
        3. Renders the 'add_vehicle.html' template, passing the 'client_id', the 'form', 
           and the current user's data to the template for display and contextual actions.

    POST Request:
        1. Validates the submitted form data using the 'validate_on_submit()' method 
           of the 'VehicleForm' class.
        2. If validation passes:
            * Extracts the form data (plate number, make, model, etc.).
            * Creates a new 'Vehicle' object, populating its attributes with the form data 
               and associating it with the correct client using 'client_id'.
            * Adds the new 'Vehicle' object to the database session using 'db.session.add()'.
            * Commits the changes to the database using 'db.session.commit()'.
            * Displays a "success" message using Flask's 'flash' functionality.
            * Redirects the user to the client's detail page to display the newly added vehicle.

        3. If validation fails:
            * Displays an "error" message using the 'flash' functionality.
            * Re-renders the 'add_vehicle.html' template with the form, allowing the user to 
               see the errors and make corrections.
    """
    client = Client.query.filter_by(client_id=client_id).first()

    form = VehicleForm()
    if request.method == 'POST': 
        if form.validate_on_submit():
            plate_num = request.form.get("plate_num")  
            owners_name = client.first_name + client.last_name
            make  = request.form.get("make")  
            model = request.form.get("model")
            color = request.form.get("color")  

            new_vehicle = Vehicle(
                client_id=client.client_id, 
                plate_num=plate_num, 
                owners_name=owners_name,
                make=make,
                model = model,
                color = color
            )
            if not plate_num or not owners_name or not make or not model or not color:
                flash("You must enter all details", 'error')
                return render_template("add_vehicle.html", form=VehicleForm(obj=new_vehicle), user=current_user, client_id = client.client_id)
            # Uniqueness Check 
            if Vehicle.query.filter_by(plate_num=plate_num).first():
                flash("A vehicle with this plate number already exists.", 'error')
                return render_template("add_vehicle.html", form=VehicleForm(obj=new_vehicle), user=current_user, client_id = client.client_id)
         
            

            try:
                db.session.add(new_vehicle)
                db.session.commit()
                try:
                    send_notification_email(
                        recipient_email=client.email,  
                        subject="Vehicle Added",
                        template="vehicle_added.html",
                        client_name=client.first_name,  # Adjust if necessary
                        plate_num=new_vehicle.plate_num,
                        make=new_vehicle.make,
                        model=new_vehicle.model,
                        color = new_vehicle.color,
                    )
                except Exception as e:
                    flash(str(e))
                
                flash("Vehicle added!", 'success')
                return redirect(url_for('client_routes.client_detail', client_id = client.client_id)) # Redirect to a success page
            except Exception as e:
                flash(f"An error occurred: {str(e)}", 'error')
                return render_template("add_vehicle.html", form=VehicleForm(obj=new_vehicle), user=current_user, client_id = client.client_id)
    return render_template("add_vehicle.html",client_id = client.client_id,  form=form, user=current_user) 


@vehicle_routes.route('/update_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def update_vehicle(vehicle_id):
    """
    Handles the modification of an existing vehicle.

    GET Request:
        1. Retrieves the 'Vehicle' object using the 'vehicle_id' from the database. If the vehicle 
           is not found, displays an "error" message and redirects.
        2. Creates an instance of the 'VehicleForm' class and populates it with the existing
           vehicle data. 
        3.  Renders the 'update_vehicle.html' template, passing the 'form', the 'vehicle_id',   
            and the current user's data to the template for display and contextual actions.

    POST Request:
        1. Validates submitted form data using the 'validate_on_submit()' method of the 'VehicleForm'.
        2. If validation passes:
            * Updates the attributes of the 'vehicle' object by calling the 'form.populate_obj(vehicle)' method. 
               This efficiently transfers data from the validated form to the object. 
            * Commits the changes to the database using 'db.session.commit()'.
            * Displays a "success" message using 'flash'. 
            * Redirects the user to the updated vehicle's detail page (within the relevant client's context).
       3. If validation fails:
            * Displays an "error" message using the 'flash' functionality.
            *  Re-renders the 'update_vehicle.html' template with the form, allowing the user to see 
               the errors and make corrections. (Also returns a 400 Bad Request HTTP status code).
    """

    vehicle = Vehicle.query.filter_by(vehicle_id=vehicle_id).first()
    client = Client.query.filter_by(client_id=vehicle.client_id).first()
    if not vehicle:
        flash("Vehicle not found", 'error')
        return redirect(url_for('home_routes.home'))  # Redirect to appropriate page

    form = VehicleForm(obj=vehicle) 

    if request.method == 'POST':  
       
        if form.validate_on_submit():

            existing_vehicle = Vehicle.query.filter(
                                Vehicle.plate_num == form.plate_num.data,
                                Vehicle.vehicle_id != vehicle_id
                            ).first()
            if existing_vehicle and existing_vehicle.vehicle_id != vehicle_id:  # Check if another vehicle has the same plate number
                flash("A vehicle with this plate number already exists.", 'error')
                return render_template("update_vehicle.html", form=form, vehicle_id=vehicle_id, user=current_user), 400 
            form.populate_obj(vehicle)
            db.session.commit()
            try:
                send_notification_email(
                        recipient_email=client.email,  
                        subject="Vehicle Update",
                        template="vehicle_updated.html",
                        client_name=client.first_name,  # Adjust if necessary
                        plate_num=vehicle.plate_num,
                        make=vehicle.make,
                        model=vehicle.model,
                        color = vehicle.color,
                    )
            except Exception as e:
                flash(str(e))
            flash("Vehicles updated!", 'success')
            return redirect(url_for('client_routes.client_detail', client_id=vehicle.client_id))  # Redirect to success page
        else:
            flash("There were errors in the form. Please correct them.", 'error')
            return render_template("update_vehicle.html", form=form, vehicle_id=vehicle_id, user=current_user), 400 

    # GET request
    return render_template("update_vehicle.html", form=form, vehicle_id=vehicle_id, user=current_user) 


@vehicle_routes.route('/delete_vehicle/<vehicle_id>' , methods=["GET", "POST"])
@login_required
def delete_vehicle(vehicle_id):
    """
    Handles the deletion of a vehicle.

    GET Request:
        1. Retrieves the 'Vehicle' object using the 'vehicle_id' from the database. If the vehicle
           is not found, displays an "error" message and redirects the user back to the client's
           detail page. 
        2. Creates an instance of the 'DeleteVehicleForm' (likely for confirmation purposes).
        3. Renders the 'delete_vehicle.html' template, passing the 'form', the 'vehicle' object, 
           and the current user's data.

    POST Request:
        1. Checks if the HTTP method is 'POST' and if the form's '_method' field is set to 'DELETE'.
           This generally indicates confirmation of the deletion action.
        2. If confirmed:
            * Deletes the 'Vehicle' object from the database using 'db.session.delete()'.
            * Commits the changes to the database using 'db.session.commit()'.
            * Displays a "success" message using the 'flash' functionality.
            * Redirects the user to the client's detail page.
        3. If the user cancels or the request is unexpected, redirects to the client's detail page.
    """
    vehicle = Vehicle.query.filter_by(vehicle_id=vehicle_id).first()
    client = Client.query.filter_by(client_id=vehicle.client_id).first()
    if not vehicle:
        flash("Vehicle not found", 'error')
        return redirect( url_for('client_routes.client_detail', client_id =vehicle.client_id )) 

    if request.method == 'POST':  
        if request.form.get('_method') == 'DELETE': # Check for Delete button
                db.session.delete(vehicle)
                db.session.commit()
                try:
                    send_notification_email(
                        recipient_email=client.email,  
                        subject="Vehicle Deleted",
                        template="vehicle_deleted.html",
                        client_name=client.first_name + " " + client.last_name,  # Adjust if necessary
                        plate_num=vehicle.plate_num,
                        make=vehicle.make,
                        model=vehicle.model,
                        color = vehicle.color,
                    )
                except Exception as e:
                    flash(str(e))
                flash("Vehicle deleted!", 'success')
                return redirect(url_for('client_routes.client_detail', client_id =vehicle.client_id )) 
        else:  # 'Cancel' or unexpected behavior
                return redirect(url_for('client_routes.client_detail', client_id =vehicle.client_id )) # Go back home

    form = DeleteVehicleForm()  
    return render_template("delete_vehicle.html", form=form, vehicle=vehicle, user=current_user) 


from sqlalchemy import or_ 
@vehicle_routes.route('/search_vehicles<client_id>') 
def search_vehicles(client_id):
    """
    Handles searching for vehicles associated with a specific client.

    1. Retrieves the search term from the query string (e.g., '.../search_vehicles?search_term=toyota'). 
       Handles the case if the search term is empty.
    2. Retrieves the 'Client' object using the provided 'client_id'. If the client is not found,
       a 404 error is raised. 
    3. Queries the database to find vehicles:
        * Filters the client's vehicles ('client.vehicles').
        * Orders the results in descending order by their make. 
        * Applies a dynamic filter using SQLAlchemy's 'or_' and 'like' operations, allowing the search
          to match against the vehicle's plate number, make, or color.
        * The '%{search_term}%' pattern enables partial matches (e.g., finding 'Toyota' if the user 
          searches for 'Toy').
    4. Renders the 'client_detail.html' template, passing the client object, the filtered vehicle records,
       and the current user's information for display.
    """
    search_term = request.args.get('search_term') or ''  # Handle empty search
    client = Client.query.filter_by(client_id=client_id).first_or_404()
    vehicle_records = client.vehicles.order_by(Vehicle.make.desc()) \
                             .filter(or_(
                                 Vehicle.plate_num.like(f'%{search_term}%'),
                                 Vehicle.make.like(f'%{search_term}%'),
                                 Vehicle.color.like(f'%{search_term}%')
                             )).all()


    return render_template('client_detail.html', client=client, vehicle_records=vehicle_records, user=current_user) 

if __name__ == '__main__':
    None