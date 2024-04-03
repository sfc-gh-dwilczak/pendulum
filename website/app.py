from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
import subprocess
import sqlite3
import os
import json
import re
import threading
import random
import time
import threading

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'py'}
DATABASE = 'results.db'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Extensions
socketio = SocketIO(app)

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY,
                output TEXT
            )''')
        conn.commit()

init_db()

# Allowed file check
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            run_script_in_background(filepath)
            return redirect(url_for('results'))
    return render_template('main/home.html')

def run_script_in_background(script_path):
    try:
        output = subprocess.check_output(['python3', script_path], stderr=subprocess.STDOUT, text=True)
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO results (output) VALUES (?)', (output,))
            conn.commit()
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e.output}")

@app.route('/results')
def results():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('SELECT output FROM results')
        data = [{'output': row[0]} for row in c.fetchall()]
    return render_template('main/results.html', results=data)

@app.route('/code')
def code():
    return render_template('main/code.html')

@app.route('/run_code', methods=['POST'])
def run_code():
    code_data = request.json.get('code', '')
    if not code_data:
        return jsonify({'error': 'No code provided'}), 400
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_code.py')
    with open(temp_filepath, 'w') as temp_file:
        temp_file.write(code_data)
    output = run_script_and_get_output(temp_filepath)
    return jsonify({'message': 'Code executed successfully', 'output': output})

def run_script_and_get_output(script_path):
    try:
        return subprocess.check_output(['python3', script_path], stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        return e.output  # Make sure to return the error output for debugging purposes.


@app.route('/live_plot')
def live_plot():
    return render_template('main/live_plot.html')

@socketio.on('encoder_data')
def handle_encoder_data(data):
    print('Received encoder data:', data)
    socketio.emit('update_data', data)  # Broadcasting received data

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
