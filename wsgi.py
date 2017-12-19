#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Author:JackYao

import sys
from os.path import abspath, dirname

sys.path.insert(0, abspath(dirname(__file__)))

from app import app

# 必须有一个叫 application 的变量
# gunicorn 就要这个变量
# 没有为什么,必须要这个文件..

application = app.app
