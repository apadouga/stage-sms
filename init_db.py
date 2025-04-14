from app import app, db  # importe l'app Flask et SQLAlchemy
from modelsDb import *     # importe tes modèles

with app.app_context():
    db.create_all()
    print("Base de données créée.")
