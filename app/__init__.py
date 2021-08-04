from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import timedelta

from flask_jwt_extended import JWTManager

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

app.config["JWT_SECRET_KEY"] = "8as4d8as4asd48asd8asd4asd8"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
jwt = JWTManager(app)

socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=3000, ping_interval=3000)


from app.request import *

