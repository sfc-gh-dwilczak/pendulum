from flask import Flask, request, redirect, url_for, render_template
import subprocess
import sqlite3
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'py'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize the database
def init_db():
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY,
            output TEXT
        )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            run_script_in_background(filepath)
            return redirect(url_for('results'))
    return render_template('main/home.html')

def run_script_in_background(script_path):
    """Run the given script and store its output in the database."""
    try:
        output = subprocess.check_output(['python', script_path], text=True)
        conn = sqlite3.connect('results.db')
        c = conn.cursor()
        c.execute('INSERT INTO results (output) VALUES (?)', (output,))
        conn.commit()
        conn.close()
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")

@app.route('/results')
def results():
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    c.execute('SELECT * FROM results')
    results = c.fetchall()
    conn.close()
    return render_template('main/results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
