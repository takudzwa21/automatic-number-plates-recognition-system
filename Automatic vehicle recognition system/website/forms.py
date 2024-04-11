from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class ClientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Add Client')

class DeleteClientForm(FlaskForm):
    submit = SubmitField('Confirm Delete')

class VehicleForm(FlaskForm):
    plate_num = StringField('Plate Number', validators=[DataRequired()])
    
    makes = [('toyota', 'Toyota'),
 ('ford', 'Ford'),
 ('chevrolet', 'Chevrolet'),
 ('honda', 'Honda'),
 ('hyundai', 'Hyundai'),
 ('nissan', 'Nissan'),
 ('volkswagen', 'Volkswagen'),
 ('jeep', 'Jeep'),
 ('ram', 'Ram Trucks'),  # Dodge Ram Trucks are now simply called Ram Trucks
 ('subaru', 'Subaru'),
 ('bmw', 'BMW'),
 ('mercedes-benz', 'Mercedes-Benz'),
 ('audi', 'Audi'),
 ('lexus', 'Lexus'),
 ('acura', 'Acura'),
 ('infiniti', 'Infiniti'),
 ('kia', 'Kia'),
 ('mazda', 'Mazda')]
    
    models = [('toyota', 'Corolla'),
('ford', 'F-150'),
('chevrolet', 'Silverado'),
('honda', 'Civic'),
('hyundai', 'Sonata'),
('nissan', 'Altima'),
('volkswagen', 'Jetta'),
('jeep', 'Wrangler'),
('ram', '1500'),  # Ram 1500 is a popular model
('subaru', 'Impreza'),
('bmw', '3 Series'),
('mercedes-benz', 'C-Class'),
('audi', 'A4'),
('lexus', 'ES'),
('acura', 'MDX'),
('infiniti', 'QX50'),
('kia', 'Telluride'),
('mazda', 'CX-5')]
    
    colors = [
    ('red', 'Red'),
    ('blue', 'Blue'),
    ('green', 'Green'),
    ('black', 'Black'),
    ('white', 'White'),
    ('silver', 'Silver'),
    ('gray', 'Gray'),
    ('navy', 'Navy Blue'),
    ('maroon', 'Maroon'),
    ('teal', 'Teal'),
    ('purple', 'Purple'),
    ('orange', 'Orange'),
    ('yellow', 'Yellow'),
    ('lime green', 'Lime Green'),
    ('forest green', 'Forest Green'),
    ('gold', 'Gold'),
    ('pink', 'Pink'),
    ('khaki', 'Khaki'),
    ('beige', 'Beige'),
    ('turquoise', 'Turquoise'),
    ('brown', 'Brown'),
]

    # Create dropdown fields
    make = SelectField('Make', choices=makes, validators=[DataRequired()])
    model = SelectField('Model', choices=models, validators=[DataRequired()])  # Initially empty
    color = SelectField('Color', choices=colors, validators=[DataRequired()])
    submit = SubmitField('Add Vehicle')


class DeleteVehicleForm(FlaskForm):
    submit = SubmitField('Confirm Delete')
