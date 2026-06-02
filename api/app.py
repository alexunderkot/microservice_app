from flask import Flask, jsonify
from prometheus_client import Counter, generate_latest, REGISTRY
import os
import json
from datetime import datetime
import logging
import sys

# JSON-логирование
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'service': 'api',
            'message': record.getMessage(),
            'logger': record.name,
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

app = Flask(__name__)
COUNTER_FILE = '/data/counter.json'

# elasticsearch logs
es = Elasticsearch(
    [os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch:9200')],
    request_timeout=30
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# jaeger
provider = TracerProvider()
trace.set_tracer_provider(provider)

otlp_endpoint = "http://jaeger:4318/v1/traces"
exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

span_processor = BatchSpanProcessor(exporter)
provider.add_span_processor(span_processor)

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

# Prometheus-метрики
CLICKS_TOTAL = Counter('app_clicks_total', 'Total button clicks')
API_REQUESTS = Counter('api_requests_total', 
                       'Total API requests', ['endpoint'])


def read_data():
    if not os.path.exists(COUNTER_FILE):
        return {'counter': 0, 'history': []}
    with open(COUNTER_FILE, 'r') as f:
        return json.load(f)


def write_data(data):
    os.makedirs('/data', exist_ok=True)
    with open(COUNTER_FILE, 'w') as f:
        json.dump(data, f)


@app.route('/metrics')
def metrics():
    return generate_latest(REGISTRY), 200, {'Content-Type': 'text/plain'}


@app.route('/health')
def health():
    API_REQUESTS.labels(endpoint='health').inc()
    return jsonify({'status': 'ok', 'service': 'api'})


@app.route('/counter')
def get_counter():
    API_REQUESTS.labels(endpoint='counter').inc()
    data = read_data()
    return jsonify({'counter': data['counter']})


@app.route('/increment', methods=['POST'])
def increment():
    API_REQUESTS.labels(endpoint='increment').inc()
    data = read_data()
    data['counter'] += 1
    data['history'].append({
        'action': 'increment',
        'timestamp': datetime.now().isoformat(),
        'value': data['counter']
    })
    if len(data['history']) > 100:
        data['history'] = data['history'][-100:]
    write_data(data)
    CLICKS_TOTAL.inc()
    logger.info('Counter incremented', extra={'counter_value': data['counter']})  # <- добавили
    return jsonify({'counter': data['counter']})


@app.route('/history')
def history():
    API_REQUESTS.labels(endpoint='history').inc()
    data = read_data()
    return jsonify({'history': data['history'][-20:]})


def send_log_to_elasticsearch(level, service, message, extra=None):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'service': service,
        'message': message,
        'extra': extra or {}
    }
    try:
        es.index(index='app-logs', body=log_entry)
    except Exception as e:
        logger.error(f"Failed to send log to Elasticsearch: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)