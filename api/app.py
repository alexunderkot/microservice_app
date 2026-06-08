import os
from flask import Flask, jsonify
from prometheus_client import Counter, generate_latest, REGISTRY
import json
from datetime import datetime
import logging
import sys
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
import redis

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

otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
provider = TracerProvider(resource=Resource.create({"service.name": "api"}))
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

FlaskInstrumentor().instrument_app(app)

# Prometheus-метрики
CLICKS_TOTAL = Counter('app_clicks_total', 'Total button clicks')
API_REQUESTS = Counter('api_requests_total', 
                       'Total API requests', ['endpoint'])

redis_client = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis-service'), port=6379, decode_responses=True)

def read_data():
    counter = redis_client.get('counter')
    history = redis_client.lrange('history', -100, -1)
    return {
        'counter': int(counter) if counter else 0,
        'history': [json.loads(h) for h in history]
    }

def write_data(data):
    redis_client.set('counter', data['counter'])
    if data['history']:
        last = data['history'][-1]
        redis_client.rpush('history', json.dumps(last))
        redis_client.ltrim('history', -100, -1)


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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)