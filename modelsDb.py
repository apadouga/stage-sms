from flask_login import UserMixin

from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class MessageDb(db.Model):
    __tablename__ = 'message_db'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(10))  # 'code', 'msg' ou 'rdv'
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    dateRDV = db.Column(db.DateTime, nullable=True)  # nouvelle colonne pour les messages de type 'rdv'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # lien obligatoire

    def to_dict(self):
        return {
            "id": self.id,
            "number": self.number,
            "content": self.content,
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "dateRDV": self.dateRDV,
            "user_id": self.user_id
        }

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    messages = db.relationship('MessageDb', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
