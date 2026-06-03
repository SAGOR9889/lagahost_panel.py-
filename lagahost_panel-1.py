import os
import subprocess
import signal
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
UPLOAD_FOLDER = 'uploaded_bots'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

running_bots = {}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LagaHost - Panel</title>
</head>
<body>
<h1>LagaHost Panel</h1>
</body>
</html>
"""

@app.route('/')
def index():
    all_files = os.listdir(app.config['UPLOAD_FOLDER'])
    bot_files = [f for f in all_files if f.endswith('.py')]
    return render_template_string(HTML_TEMPLATE, bots=bot_files, running_bots=running_bots)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'bot_file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['bot_file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file and file.filename.endswith('.py'):
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
