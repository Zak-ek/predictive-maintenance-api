from flask import Flask
from app.database import db, init_db
from app.routes import api


def create_app():
    app = Flask(__name__)
    
    init_db(app)
    
    app.register_blueprint(api, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
    
    return app