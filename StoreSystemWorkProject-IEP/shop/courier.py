from flask import Flask, request, make_response, jsonify, Response
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from decorators import roleCheck
from configuration import Configuration
from models import db, Product, Category, Order, Reserved
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Configuration)
jwt = JWTManager(app)


@app.route('/orders_to_deliver', methods=['GET'])
@roleCheck("courier")
@jwt_required()
def getOrdersToBeDelivered():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

    orders = Order.query.filter(Order.status == 'CREATED').all()

    response = [{"id": order.id, "email": order.customer} for order in orders]
    return make_response(jsonify({"orders": response}), 200)


@app.route('/pick_up_order', methods=['POST'])
@roleCheck("courier")
@jwt_required()
def pickUpOrder():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)
    if 'id' not in request.json:
        obj = {'message': 'Missing order id.'}
        return make_response(jsonify(obj), 400)

    orderId = request.json.get("id", "")
    if orderId == "":
        obj = {'message': 'Missing order id.'}
        return make_response(jsonify(obj), 400)
    if type(orderId) != int or orderId <= 0:
        obj = {'message': 'Invalid order id.'}
        return make_response(jsonify(obj), 400)
    order = Order.query.filter(Order.id == orderId).first()
    if order is None:
        obj = {'message': 'Invalid order id.'}
        return make_response(jsonify(obj), 400)
    elif order.status != 'CREATED':
        obj = {'message': 'Invalid order id.'}
        return make_response(jsonify(obj), 400)

    order.status = 'PENDING'
    db.session.commit()

    return Response(status=200)


@app.route("/", methods=["GET"])
def index():
    return "Hello from courier"


if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=True, host='0.0.0.0', port=5003)
