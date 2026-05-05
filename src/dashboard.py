from flask import Flask, render_template, jsonify
import pandas as pd
import os
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>IG Creator PRO Dashboard</title>
        <style>
            body { font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; }
            .card { background: #2d2d2d; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            h1 { color: #e1306c; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; border: 1px solid #444; text-align: left; }
            .success { color: #4caf50; }
        </style>
        <script>
            setInterval(() => { location.reload(); }, 5000);
        </script>
    </head>
    <body>
        <h1>🚀 Instagram Account Creator PRO</h1>
        <div class="card">
            <h2>Live Statistics</h2>
            <div id="stats">Checking accounts...</div>
        </div>
        <div class="card">
            <h2>Created Accounts</h2>
            <div id="table">
                %s
            </div>
        </div>
    </body>
    </html>
    """ % get_table_html()

def get_table_html():
    if not os.path.exists("accounts.csv"):
        return "No accounts created yet."
    try:
        df = pd.read_csv("accounts.csv")
        return df.to_html(classes="table")
    except:
        return "Loading..."

def run_dashboard():
    app.run(port=5050, host='0.0.0.0')

if __name__ == "__main__":
    run_dashboard()
