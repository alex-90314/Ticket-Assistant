# keep_alive.py
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return f"I'm alive! \n Production branch - Update 1.3"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
