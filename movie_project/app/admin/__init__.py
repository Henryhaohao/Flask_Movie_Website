# !/user/bin/env python
# -*- coding:utf-8 -*- 
# time: 2018/3/7--19:51
__author__ = 'Henry'

from flask import Blueprint

admin = Blueprint('admin',__name__)

import app.admin.views

