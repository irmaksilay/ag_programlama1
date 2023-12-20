from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, join_room, leave_room
import requests
import threading
import os

# API key ve base URL
# file deepcode ignore HardcodedNonCryptoSecret: <NOT IMPORTANT>
ACCESS_KEY = '970ef16acdcd560bb68273408984fa9f'
URL = f'http://data.fixer.io/api/latest?access_key={ACCESS_KEY}'

app = Flask(__name__)
socketio = SocketIO(app)

template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server')
app = Flask(__name__, template_folder="templates")

def get_exchange_rate(from_currency, to_currency):
    response = requests.get(URL)
    rates = response.json()['rates']

    rate = rates[to_currency] / rates[from_currency]

    return rate

def update_exchange_rate():
    while True:
        usd_try_rate = get_exchange_rate("USD", "TRY")
        eur_try_rate = get_exchange_rate("EUR", "TRY")
        print("USD/TRY: ", round(usd_try_rate, 5))
        print("EUR/TRY: ", round(eur_try_rate, 5))

        socketio.emit('update_rate_usd_try', {'rate': round(usd_try_rate, 5)})
        socketio.emit('update_rate_eur_try', {'rate': round(eur_try_rate, 5)})
        socketio.sleep(2)  

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dynamic')
def convert():
    return render_template('dynamic.html')

@app.route('/static')
def index():
    return render_template('static.html')

@app.route('/multi_thread')
def multi_thread():
    if 'username' in session:
        return render_template('multi-thread.html', username=session['username'])
    return render_template('multi-thread.html')


@socketio.on('message_from_client')
def handle_message_from_client(message):
    print(f"Message from client: {message}")
    socketio.emit('message_from_server', f"Server says: {message}")

@socketio.on('message_from_server')
def handle_message_from_server(message):
    print(f"Message from server: {message}")
    socketio.emit('message_from_client', f"Client says: {message}")

@socketio.on('user_joined')
def handle_user_joined(data):
    username = data['username']
    message = f'{username} joined the chat'
    socketio.emit('message', {'username': 'SERVER', 'message': message})

@socketio.on('send_message')
def handle_send_message(data):
    socketio.emit('message', data)

@socketio.on('disconnect')
def handle_disconnect():
    leave_room('chat')

if __name__ == '__main__':
    # Arka planda oranı güncelleyen bir thread başlat
    # file deepcode ignore MissingAPI: <NOT IMPORTANT>
    update_thread = threading.Thread(target=update_exchange_rate)
    update_thread.daemon = True
    update_thread.start()
    socketio.run(app, debug=True)