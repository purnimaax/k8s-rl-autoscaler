from flask import Flask, request
import time
import math

app = Flask(__name__)

def burn_cpu(duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = math.sqrt(64*64*64*64*64) 

@app.route('/')
def health():
    return "CPU-Eater is Ready!", 200

@app.route('/stress')
def stress():
    duration = float(request.args.get('duration', 0.5))
    burn_cpu(duration)
    return f"Burned CPU for {duration} seconds.\n", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)