from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


db = SQLAlchemy()

bcrypt = Bcrypt()

def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)

class User(db.Model):
    @classmethod
    def register(cls, username, pwd):
        hashed = bcrypt.generate_password_hash(pwd)
        hashed_utf8 = hashed.decode("utf8")

        return cls(username=username, password=hashed_utf8)
    
    @classmethod
    def authenticate(cls, username, pwd):
        u = User.query.filter_by(username=username).first()
        if u and bcrypt.check_password_hash(u.password, pwd):
            return u 
        else:
            return False
        
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    first_name = db.Column(db.String(30), nullable=False)

    last_name = db.Column(db.String(30), nullable=False)

    username = db.Column(db.String(20), nullable=False, unique=True)

    email = db.Column(db.String(50), nullable=False)

    password = db.Column(db.String, nullable=False)

    feedback = db.relationship('Feedback', backref='users', cascade='all, delete')


    def __repr__(self):
        """Displaying User"""

        u = self 
        return f"<id={u.id}, first name={u.first_name}, last name={u.last_name}, username ={u.username}>"
    


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String, nullable=False)

    username = db.Column(db.String(20), db.ForeignKey('users.username'), nullable=False)


    