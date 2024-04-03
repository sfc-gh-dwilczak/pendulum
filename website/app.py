from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import traceback
import sys
from io import StringIO


import sqlite3
import os
import json
import re
import sys
import traceback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///code_snippets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CodeSnippet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    code = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text)  # New column for storing execution results

def initialize_database():
    with app.app_context():
        db.create_all()


@app.route('/', methods=['GET', 'POST'])
def home():
    first_snippet = CodeSnippet.query.first()
    filenames = CodeSnippet.query.with_entities(CodeSnippet.filename).all()
    filenames = [filename[0] for filename in filenames]  # Flatten the list of tuples
    
    # Initialize variables in case there are no snippets
    first_filename = ''
    first_code = ''
    first_result = ''
    
    if first_snippet:
        first_filename = first_snippet.filename
        first_code = first_snippet.code
        first_result = first_snippet.result  # Get the execution result of the first snippet
    
    return render_template('main/home.html', 
                           first_filename=first_filename, 
                           first_code=first_code, 
                           first_result=first_result, 
                           filenames=filenames)

@app.route('/run_code', methods=['POST'])
def run_code():
    code = request.form.get('code')
    filename = request.form.get('filename')

    # Redirect standard output
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    try:
        exec_globals = {}
        exec(code, exec_globals)
        sys.stdout = old_stdout  # Reset standard output to original
        result = redirected_output.getvalue()
    except Exception as e:
        sys.stdout = old_stdout  # Reset standard output to original
        result = f"Error: {traceback.format_exc()}"
    finally:
        redirected_output.close()

    # Check if the filename already exists
    snippet = CodeSnippet.query.filter_by(filename=filename).first()

    if snippet:
        # Update existing code and result
        snippet.code = code
        snippet.result = result  # Save the execution result
    else:
        # Create a new code snippet with result
        snippet = CodeSnippet(filename=filename, code=code, result=result)
        db.session.add(snippet)

    db.session.commit()

    return jsonify(result=result or "Code executed with no output.")


@app.route('/get_code_by_filename')
def get_code_by_filename():
    filename = request.args.get('filename')
    snippet = CodeSnippet.query.filter_by(filename=filename).first()
    if snippet:
        return jsonify({"filename": snippet.filename, "code": snippet.code, "result": snippet.result})
    return jsonify({"error": "Snippet not found"}), 404

@app.route('/save_code', methods=['POST'])
def save_code():
    code = request.form.get('code')
    filename = request.form.get('filename')

    if not filename:  # Validate filename presence
        return jsonify({"error": "Filename is required."}), 400

    snippet = CodeSnippet.query.filter_by(filename=filename).first()

    if snippet:
        snippet.code = code  # Update existing code snippet
    else:
        new_snippet = CodeSnippet(filename=filename, code=code)  # Create new snippet
        db.session.add(new_snippet)
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "Code saved successfully."})

@app.route('/results')
def results():
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    c.execute('SELECT output FROM results')
    results = c.fetchall()
    conn.close()

    data = []

    for result in results:
        # Extract the string from the tuple
        json_string = result[0]

        # Use regular expression to extract valid JSON objects
        json_objects = re.findall(r'\{[^}]+\}', json_string)

        # Parse each JSON object and append it to a list
        dicts = [json.loads(obj) for obj in json_objects]
        data.append(dicts)
    
    return render_template('main/results.html', results=data[1])

@app.route('/get_first_snippet')
def get_first_snippet():
    # Attempt to get the first code snippet from the database
    first_snippet = CodeSnippet.query.first()
    
    if first_snippet:
        # If a snippet is found, return its details
        return jsonify({
            "filename": first_snippet.filename,
            "code": first_snippet.code,
            "result": first_snippet.result
        })
    else:
        # If no snippets are found, return an appropriate message
        return jsonify({"error": "No snippets found."}), 404

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True, host='0.0.0.0')
