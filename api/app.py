from flask import Flask, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)
COUNTER_FILE = '/data/counter.json'


def read_data():
    if not os.path.exists(COUNTER_FILE):
        return {'counter': 0, 'history': []}
    with open(COUNTER_FILE, 'r') as f:
        return json.load(f)


def write_data(data):
    os.makedirs('/data', exist_ok=True)
    with open(COUNTER_FILE, 'w') as f:
        json.dump(data, f)


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'api'})


@app.route('/counter')
def get_counter():
    data = read_data()
    return jsonify({'counter': data['counter']})


@app.route('/increment', methods=['POST'])
def increment():
    data = read_data()
    data['counter'] += 1
    data['history'].append({
        'action': 'increment',
        'timestamp': datetime.now().isoformat(),
        'value': data['counter']
    })
    # Храним только последние 100 записей
    if len(data['history']) > 100:
        data['history'] = data['history'][-100:]
    write_data(data)
    return jsonify({'counter': data['counter']})


@app.route('/history')
def history():
    data = read_data()
    return jsonify({'history': data['history'][-20:]})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)