# -*- coding: utf-8 -*-

from flask import Flask, render_template

app = Flask(__name__)
app.debug = True

from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint
from app.api import api as api_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix="/admin")
app.register_blueprint(api_blueprint, url_prefix="/api")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
