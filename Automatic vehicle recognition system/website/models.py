from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Client(db.Model):
    client_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique = True)
    vehicles = db.relationship('Vehicle', backref='client', lazy='dynamic')
    entry_approvals = db.relationship('EntryApproval', backref='client', lazy=True)

    def get_id(self):
        return str(self.client_id)

class Vehicle(db.Model):
    vehicle_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.client_id'), nullable=False)
    plate_num = db.Column(db.String(255), nullable=False, unique = True)
    owners_name = db.Column(db.String(255), nullable=False)
    make = db.Column(db.String(255), nullable=False)
    model = db.Column(db.String(255), nullable=False)
    color = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return str(self.vehicle_id)

class EntryApproval(db.Model):
    approval_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.client_id'), nullable=True)
    guard_id = db.Column(db.Integer, db.ForeignKey('guard.guard_id'), nullable=True)
    approval_status = db.Column(db.Boolean, nullable=False)
    approval_time = db.Column(db.DateTime, nullable=False)

    def get_id(self):
        return str(self.approval_id)

    @property
    def status(self):
        return "Approved" if self.approval_status else "Denied"
    
class LoginLogout(db.Model):
    entry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    guard_id = db.Column(db.Integer, db.ForeignKey('guard.guard_id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.client_id'), nullable=False)
    login_time = db.Column(db.DateTime, nullable=False)
    logout_time = db.Column(db.DateTime, nullable=True)
    plate_num = db.Column(db.String(255), nullable=False, unique = False)
    

    def get_id(self):
        return str(self.entry_id)


class Guard(db.Model, UserMixin):
    guard_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    entry_logs = db.relationship('LoginLogout', backref='guard', lazy=True)
    supervisor = db.Column(db.Boolean, nullable=False)
    suspended = db.Column(db.Boolean, nullable=False)

    def get_id(self):
        return str(self.guard_id)