#!/usr/bin/env python
# __author__ = lvhuiyang

import time
from flask import Flask
from celery import Celery

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost:5672//'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task
def add_together(a, b):
    result = a + b
    print("result is {}".format(result))
    time.sleep(3)
    return True


@app.route("/")
def hello():
    add_together.delay(23, 42)
    return 'Hello World'


if __name__ == '__main__':
    app.run(debug=True)
