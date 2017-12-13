# -*- coding: utf-8 -*-


from . import admin
from flask import render_template, redirect, url_for, Response
import json


@admin.route("/")
def index():
    return render_template('admin/index.html')


@admin.route('/getName')
def name():
    return Response(json.dumps({'name': 'jack'}), mimetype='application/json')


@admin.route('/login')
def login():
    return render_template('admin/login.html')


@admin.route('/logout')
def logout():
    return redirect(url_for('admin.login'))


@admin.route("/pwd")
def pwd():
    return render_template('admin/pwd.html')
