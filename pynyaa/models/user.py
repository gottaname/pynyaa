
from flask_login import UserMixin
from flask_scrypt import generate_password_hash, generate_random_salt, check_password_hash

from .. import db


class UserStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)

    signed_up_date = db.Column(db.DateTime(True))

    status_id = db.Column(db.Integer, db.ForeignKey('user_status.id'))
    status = db.relationship('UserStatus', backref='users')

    hashed_password = db.Column(db.String(255))
    password_salt = db.Column(db.String(100))

    @property
    def password(self):
        raise AttributeError("Cannot read password.")

    @password.setter
    def password(self, value):
        value = value.encode('utf-8')
        salt = generate_random_salt(64)
        hashed = generate_password_hash(value, salt, 1 << 14, 8, 1, 64)
        self.password_salt = salt.decode('ascii')
        self.hashed_password = hashed.decode('ascii')

    def check_password(self, value):
        value = value.encode('utf-8')
        salt = self.password_salt.encode('ascii')
        hashed = self.hashed_password.encode('ascii')
        return check_password_hash(value, hashed, salt)
