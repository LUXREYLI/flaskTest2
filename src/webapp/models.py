from flask_sqlalchemy import SQLAlchemy

# create the extension
db = SQLAlchemy()


class Account(db.Model):
    # class to manage users
    __tablename__ = 'account'
    account_id = db.Column(db.String(1), primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    password = db.Column(db.LargeBinary, nullable=True)
    initialized = db.Column(db.Boolean)


class Parameter(db.Model):
    # class to initialize the masterpassword
    __tablename__ = 'parameter'
    parameter_id = db.Column(db.SmallInteger, primary_key=True)
    password = db.Column(db.LargeBinary, nullable=True)
    initialized = db.Column(db.Boolean)


class LogInfo(db.Model):
    # class for logging
    __tablename__ = 'loginfo'
    loginfo_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(1), nullable=True)
    log_date = db.Column(db.DateTime, nullable=False)
    log_description = db.Column(db.String(100), nullable=True)
