from app import app
from app import socketio

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)