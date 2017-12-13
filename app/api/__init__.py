# -*- coding: utf-8 -*-

from flask import Blueprint

api = Blueprint("api", __name__, subdomain='api')

import app.api.views
