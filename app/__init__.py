from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)
app.config.from_pyfile('../instance/config.py')
db = SQLAlchemy(app)
migrate = Migrate(app, db, compare_type=True)

from app import routes, models
