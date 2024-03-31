from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()


class Reserved(db.Model):
    __tablename__ = 'reserved'
    id = db.Column(db.Integer, primary_key=True)
    productID = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    orderID = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    products = db.relationship('Product', secondary='reserved', backref=db.backref('orders', lazy='dynamic'))

    def serialize(self):
        return {
            "products": [product.serialize(self.id) for product in self.products],
            "price": self.price,
            "status": self.status,
            "timestamp": self.timestamp.isoformat()
        }


class ProductCategory(db.Model):
    __tablename__ = 'product_category'

    id = db.Column(db.Integer, primary_key=True)
    productID = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    categoryID = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)

    categories = db.relationship('Category', secondary='product_category',
                                 backref=db.backref('products', lazy='dynamic'))

    def get_quantity(self, orderId):
        reserved_records = Reserved.query.filter_by(productID=self.id, orderID=orderId).all()
        return len(reserved_records)

    def serialize(self, orderId):
        return {
            "categories": [category.name for category in self.categories],
            "name": self.name,
            "price": self.price,
            "quantity": self.get_quantity(orderId)
        }


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f"Category {self.id}, Name: {self.name}"
