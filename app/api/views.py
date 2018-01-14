from . import api
from flask import render_template, redirect, url_for, Response, request
import json
from google import protobuf



# 这里是提供 API 的接口
@api.route('/')
def sample():
    return Response(json.dumps({'name': 'jack'}), mimetype='application/json')


@api.route('/name', methods=['GET', 'POST'])
def fuck():
    # The parsed URL parameters
    # ?name = fuck & age = 9
    # [('name', 'fuck'), ('age', '9')] 可以直接 json 序列化
    print(request.args)
    print(request.data)
    # post parameters
    print(request.form)
    # 这是一个list [args,form]
    # print(request.values)
    print(request.headers)
    print(request.files)
    if request.method == 'GET':
        return Response(json.dumps(request.args), mimetype='application/json')
    else:
        return Response(json.dumps(request.form), mimetype='application/json')