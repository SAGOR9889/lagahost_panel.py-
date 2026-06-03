import os
import subprocess
import signal
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Vercel-এ সাময়িকভাবে ফাইল রাখার জন্য /tmp ফোল্ডার ব্যবহার করতে হয়
UPLOAD_FOLDER = '/tmp/uploaded_bots'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# রানিং বট ট্র্যাক করার ডিকশনারি
running_bots = {}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---- HTML এবং CSS ডিজাইন থিম (LagaHost-এর মতো ডার্ক মোড) ----
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LagaHost - Panel</title>
    <style>
        body {
            background-color: #0b111e;
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }
        .panel-container {
            width: 100%;
            max-width: 450px;
            background: #0d1626;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        .logo {
            font-size: 22px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .lock-btn {
            background: #dc2626;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
        }
        .upload-box {
            border: 2px dashed #1e293b;
            border-radius: 10px;
            padding: 30px 20px;
            text-align: center;
            background: #0f1a30;
            margin-bottom: 25px;
        }
        .upload-icon { font-size: 40px; color: #3b82f6; margin-bottom: 10px; }
        .deploy-btn {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: bold;
        }
        .section-title {
            font-size: 18px;
            border-left: 4px solid #2563eb;
            padding-left: 10px;
            margin-bottom: 15px;
        }
        .bot-card {
            background: #111c32;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .bot-name {
            font-size: 16px;
            font-weight: bold;
        }
        .status-badge {
            display: inline-block;
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 20px;
            margin-top: 8px;
            font-weight: bold;
        }
        .status-running { background: rgba(16, 185, 129, 0.2); color: #10b981; }
        .status-stopped { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            flex: 1;
            padding: 8px;
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font-weight: bold;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
        }
        .btn-start { background: #2563eb; }
        .btn-stop { background: #d97706; }
        .btn-delete { background: #991b1b; }
        
        .logs-box {
            background: #000000;
            color: #10b981;
            font-family: monospace;
            padding: 10px;
            border-radius: 6px;
            margin-top: 15px;
            font-size: 12px;
            max-height: 100px;
            overflow-y: auto;
        }
    </style>
</head>
<body>

<div class="panel-container">
    <div class="header">
        <div class="logo">💾 LagaHost</div>
        <button class="lock-btn">🔒 Lock Panel</button>
    </div>

    <div class="upload-box">
        <form action="/upload" method="post" enctype="multipart/form-data">
            <div class="upload-icon">☁️</div>
            <h3>Deploy New Bot</h3>
            <p style="color: #64748b; font-size: 14px;">Supported: .py</p>
            <input type="file" name="bot_file" accept=".py" required><br>
            <button type="submit" class="deploy-btn">🚀 Deploy</button>
        </form>
    </div>

    <div class="section-title">Active Projects</div>

    {% if bots %}
        {% for bot in bots %}
        <div class="bot-card">
            <div class="bot-name">🐍 {{ bot }}</div>
            
            {% if bot in running_bots %}
                <span class="status-badge status-running">● RUNNING</span>
            {% else %}
                <span class="status-badge status-stopped">● STOPPED</span>
            {% endif %}

            <div class="controls">
                <a href="/start/{{ bot }}" class="btn btn-start">▶ Start</a>
                <a href="/stop/{{ bot }}" class="btn btn-stop">■ Stop</a>
                <a href="/delete/{{ bot }}" class="btn btn-delete">🗑️</a>
            </div>

            <div class="logs-box">
                &gt; Waiting for logs...
            </div>
        </div>
        {% endfor %}
    {% else %}
        <p style="color: #64748b; text-align: center;">No bots deployed yet.</p>
    {% endif %}
</div>

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

@app.route('/start/<filename>')
def start_bot(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if filename not in running_bots:
        try:
            # সার্ভারলেস ব্যাকগ্রাউন্ড প্রসেস চালু করা
            process = subprocess.Popen(['python', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            running_bots[filename] = process.pid
        except Exception as e:
            print(f"Error starting bot: {e}")
    return redirect(url_for('index'))

@app.route('/stop/<filename>')
def stop_bot(filename):
    if filename in running_bots:
        pid = running_bots[filename]
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            pass
        del running_bots[filename]
    return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete_bot(filename):
    stop_bot(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))

# Vercel হ্যান্ডলারের জন্য অ্যাপ অবজেক্ট এক্সপোজ করা হলো
thissite = app
