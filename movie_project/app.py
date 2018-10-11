# !/user/bin/env python
# -*- coding:utf-8 -*-
# time: 2018/3/7--19:49
from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
