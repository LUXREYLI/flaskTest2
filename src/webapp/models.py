from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Account(db.Model):
    __tablename__ = 'account'
    account_id = db.Column(db.String(1), primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    initialized = db.Column(db.Boolean)

#class InfoModel(db.Model):
#    __tablename__ = 'info_table'

    #id = db.Column(db.Integer, primary_key = True)
    #name = db.Column(db.String())
    #age = db.Column(db.Integer())

    #def __init__(self, name,age):
    #    self.name = name
    #    self.age = age

    #def __repr__(self):
    #    return f"{self.name}:{self.age}"