# -*- coding: utf-8 -*-

from flask import Flask, render_template
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql

app = Flask(__name__)
app.debug = True
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@127.0.0.1:3306/movie?charset=utf8"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SECRET_KEY"] = 'sbidQvBdtqJVgMjzEuUDLYzJHoZmCtUxdcijhvedtWBVuN8ieAhjLaZJpnyDKACT'
db = SQLAlchemy(app, use_native_unicode="utf8")


from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint
from app.api import api as api_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix="/admin")
app.register_blueprint(api_blueprint, url_prefix="/api")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
