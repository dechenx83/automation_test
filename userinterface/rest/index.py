from flask import Flask, Blueprint
from flask_restplus import Api
from userinterface.rest.endpoint.runner import name_space

app = Flask(__name__)
api = Api(title="Automation Test Platfrom API", version="1.0")
bp = Blueprint("api", __name__, url_prefix="/rest")
api.init_app(bp)
api.add_namespace(name_space)
app.register_blueprint(bp)


app.run(host="0.0.0.0", port=5000)