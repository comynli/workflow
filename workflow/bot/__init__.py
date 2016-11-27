import json
import threading
from wsgiref.simple_server import make_server
from concurrent.futures import ThreadPoolExecutor
from pika import URLParameters, BlockingConnection
from collections import namedtuple
from m import Application, Router
from m.utils import jsonify


Event = namedtuple('Event', ['workflow_id', 'state_id'])


router = Router()


@router.post('/msched/callback')
def listen(ctx, request):
    payload = request.json()
    task_id = payload.get('id')
    event = ctx.tasks.get(task_id)
    event.set()
    return jsonify(code=200)


class Bot:
    def __init__(self, name, amqp_url, exchange='workflow', max_workers=None, host='0.0.0.0', port=50051):
        self.name = name
        self.url = amqp_url
        self.exchange = exchange
        self.connection = None
        self.watchers = set()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = dict()
        self.app = Application(routers=[router], tasks=self.tasks)
        self.wsgi = make_server(host=host, port=port, app=self.app)

    def register(self, state):
        self.watchers.add(state)

    def wait(self, task_id):
        event = threading.Event()
        self.tasks[task_id] = event
        event.wait()

    def work(self, event: Event):
        raise NotImplemented

    def start(self):
        t = threading.Thread(target=self.wsgi.serve_forever)
        t.daemon = True
        t.start()
        self.connection = BlockingConnection(parameters=URLParameters(self.url))
        channel = self.connection.channel()
        channel.queue_declare(queue=self.name, durable=True)
        channel.queue_bind(queue=self.name, exchange=self.exchange)
        for frame, _, msg in channel.consume(self.name):
            message = json.loads(msg.decode())
            event = Event(message['workflow'], message['state'])
            if event.state_id in self.watchers:
                self.executor.submit(self.work, event).add_done_callback(lambda: channel.basic_ack(frame.delivery_tag))

    def shutdown(self):
        self.wsgi.shutdown()
        if self.connection is not None:
            self.connection.close()
