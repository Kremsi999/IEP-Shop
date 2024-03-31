from flask import Flask, request, make_response, jsonify, Response
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from decorators import roleCheck
from configuration import Configuration
from models import db, Product, Category, Order, Reserved
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Configuration)
jwt = JWTManager(app)


@app.route('/search', methods=['GET'])
@roleCheck("customer")
@jwt_required()
def searchProducts():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

    product = request.args.get('name')
    category = request.args.get('category')

    query = db.session.query(Product)
    if product:
        query = query.filter(Product.name.like(f"%{product}%"))
    if category:
        query = query.join(Product.categories).filter(Category.name.like(f"%{category}%"))

    filteredProducts = query.all()

    response = {
        "categories": [],
        "products": []
    }
    for product in filteredProducts:
        productCategories = [category.name for category in product.categories]
        response["products"].append({
            "categories": productCategories,
            "id": product.id,
            "name": product.name,
            "price": product.price
        })
        response["categories"].extend(productCategories)

    response["categories"] = list(set(response["categories"]))

    return make_response(jsonify(response), 200)


# TODO test
@app.route('/order', methods=['POST'])
@roleCheck("customer")
@jwt_required()
def createOrder():

    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

    if 'requests' not in request.json:
        obj = {'message': 'Field requests is missing.'}
        return make_response(jsonify(obj), 400)

    additionalClaims = get_jwt()
    customer = additionalClaims["email"]

    productsInOrder = request.json.get("requests", "")
    idx = 0
    for product in productsInOrder:
        if product.get("id", "") == "":
            obj = {'message': f'Product id is missing for request number {idx}.'}
            return make_response(jsonify(obj), 400)
        if product.get("quantity", "") == "":
            obj = {'message': f'Product quantity is missing for request number {idx}.'}
            return make_response(jsonify(obj), 400)
        if type(product.get("id", "")) != int or product.get("id", "") <= 0:
            obj = {'message': f'Invalid product id for request number {idx}.'}
            return make_response(jsonify(obj), 400)
        if type(product.get("quantity", "")) != int or product.get("quantity", "") <= 0:
            obj = {'message': f'Invalid product quantity for request number {idx}.'}
            return make_response(jsonify(obj), 400)

        if Product.query.filter(Product.id == product.get("id", "")).first() is None:
            obj = {'message': f'Invalid product for request number {idx}.'}
            return make_response(jsonify(obj), 400)
        idx += 1

    order = Order(customer=customer, status="CREATED", price=0, timestamp=datetime.utcnow())
    db.session.add(order)
    db.session.commit()
    for product in productsInOrder:
        productId = product.get("id", "")
        quantity = product.get("quantity", "")
        productInOrder = Product.query.filter(Product.id == product.get("id", "")).first()
        for i in range(quantity):
            reserved = Reserved(productID=productId, orderID=order.id)
            db.session.add(reserved)
        order.price += productInOrder.price * quantity

    db.session.commit()

    return make_response(jsonify({"id": order.id}), 200)


@app.route('/status', methods=['GET'])
@roleCheck("customer")
@jwt_required()
def getOrdersStatus():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

    additionalClaims = get_jwt()
    customer = additionalClaims["email"]

    orders = Order.query.filter(Order.customer == customer).all()

    response = [order.serialize() for order in orders]
    return make_response(jsonify({"orders": response}), 200)


@app.route('/delivered', methods=['POST'])
@roleCheck("customer")
@jwt_required()
def confirmDelivery():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

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
    elif order.status != 'PENDING':
        obj = {'message': 'Invalid order id.'}
        return make_response(jsonify(obj), 400)

    order.status = 'COMPLETE'
    db.session.commit()

    return Response(status=200)


@app.route("/", methods=["GET"])
def index():
    return "Hello from customer"


if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=True, host='0.0.0.0', port=5002)
