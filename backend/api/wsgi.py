from app import app
from extensions import socketio

if __name__ == '__main__':
    print("🚀 Starting Drowsiness Detection Server with WebSocket support...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=False
    )
