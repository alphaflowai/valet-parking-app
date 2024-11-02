from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main.routes import valet, customer, general, admin, manager, utility, auth
