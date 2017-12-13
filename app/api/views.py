from . import api
from flask import render_template, redirect, url_for, Response
import json


# 这里是提供 API 的接口
@api.route('/api')
def sample():
    return Response(json.dumps({'name': 'jack'}), mimetype='application/json')
