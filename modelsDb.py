from app import db

class MessageDb(db.Model):
    __tablename__ = 'message_db'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(10))  # 'code', 'msg' ou 'rdv'
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    dateRDV = db.Column(db.DateTime, nullable=True)  # nouvelle colonne pour les messages de type 'rdv'

    def to_dict(self):
        return {
            "id": self.id,
            "number": self.number,
            "content": self.content,
            "type": self.type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "dateRDV": self.dateRDV
        }

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
