from flask import Flask, request, Response, make_response, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import func

from decorators import roleCheck
from configuration import Configuration
from models import db, Product, Category, Reserved, Order
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
import csv
import io

app = Flask(__name__)
app.config.from_object(Configuration)
jwt = JWTManager(app)


@app.route('/update', methods=['POST'])
@roleCheck("owner")
@jwt_required()
def addProducts():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

    if 'file' not in request.files:
        obj = {"message": "Field file is missing."}
        return make_response(jsonify(obj), 400)

    file = request.files['file']
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    body = csv.reader(stream)

    for idx, row in enumerate(body):
        if len(row) != 3:
            db.session.rollback()
            obj = {"message": f"Incorrect number of values on line {idx}."}
            return make_response(jsonify(obj), 400)
        categories = row[0].split('|')
        name = row[1]
        price = row[2]

        try:
            price = float(price)
            if price <= 0:
                raise ValueError
        except ValueError:
            db.session.rollback()
            obj = {"message": f"Incorrect price on line {idx}."}
            return make_response(jsonify(obj), 400)

        if Product.query.filter(Product.name == name).first():
            db.session.rollback()
            obj = {"message": f"Product {name} already exists."}
            return make_response(jsonify(obj), 400)

        product = Product(name=name, price=price)
        for categoryEl in categories:
            category = Category.query.filter(Category.name == categoryEl).first()
            if not category:
                category = Category(name=categoryEl)
            product.categories.append(category)

        db.session.add(product)

    try:
        db.session.commit()
        return Response(status=200)
    except IntegrityError:
        db.session.rollback()
        return Response(status=400)


@app.route('/product_statistics', methods=['GET'])
@roleCheck("owner")
@jwt_required()
def productStatistics():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header."}
        return make_response(jsonify(obj), 401)

    statistics = []
    products = Product.query.all()
    for product in products:
        sold = 0
        waiting = 0
        for order in product.orders:
            for orderedProduct in range(len(Reserved.query.filter(Reserved.productID == product.id,
                                                                  Reserved.orderID == order.id).all())):
                if order.status == 'COMPLETE':
                    sold += 1
                elif order.status == 'CREATED' or order.status == 'PENDING':
                    waiting += 1
        if sold > 0:
            statistics.append({
                "name": product.name,
                "sold": sold,
                "waiting": waiting
            })

    obj = {
        "statistics": statistics
    }
    return make_response(jsonify(obj), 200)


@app.route('/category_statistics', methods=['GET'])
@roleCheck("owner")
@jwt_required()
def categoryStatistics():
    if 'Authorization' not in request.headers:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

    categories = Category.query.all()
    statistics = defaultdict(int)
    for category in categories:
        statistics[category.name] = 0
    productCounts = db.session.query(func.count(Reserved.id).label('sold'), Product.name) \
        .join(Order, Order.id == Reserved.orderID) \
        .join(Product, Product.id == Reserved.productID) \
        .filter(Order.status == 'COMPLETE') \
        .group_by(Product.id) \
        .all()
    for sold, product_name in productCounts:
        product = Product.query.filter_by(name=product_name).first()
        for category in product.categories:
            statistics[category.name] += sold
    sortedStatistics = sorted(statistics.items(), key=lambda x: (-x[1], x[0]))
    result = [categoryName for categoryName, _ in sortedStatistics]

    obj = {
        "statistics": result
    }
    return make_response(jsonify(obj), 200)


@app.route("/", methods=["GET"])
def index():
    return "Hello from owner"


if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=True, host='0.0.0.0', port=5001)
