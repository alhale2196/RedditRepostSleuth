import os

# Celery is broken on windows
import sys

from celery import Celery

from redditrepostsleuth.config import config
from kombu.serialization import registry
registry.enable('pickle')

sys.setrecursionlimit(2500)
print(sys.getrecursionlimit())

if os.name =='nt':
    os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

celery = Celery('tasks', backend=config.celery_backend,
             broker=config.celery_broker)

celery.conf.update(
    task_serializer='pickle',
    result_serializer='pickle',
    accept_content=['pickle', 'json']
)


if __name__ == '__main__':
    celery.start()