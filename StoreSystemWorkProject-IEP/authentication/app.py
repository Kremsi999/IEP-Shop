from flask import Flask, request, Response, jsonify, make_response
from decorators import roleCheck
from configuration import Configuration
from models import db, User, UserRole
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_
import re

app = Flask(__name__)
app.config.from_object(Configuration)


def checkEmail(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.fullmatch(regex, email)


def checkPassword(password):
    regex = r'^.{8,256}$'
    return re.fullmatch(regex, password)


@app.route("/register_customer", methods=["POST"])
def registerCustomer():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    if len(forename) == 0:
        obj = {"message": "Field forename is missing."}
        return make_response(jsonify(obj), 400)

    if len(surname) == 0:
        obj = {"message": "Field surname is missing."}
        return make_response(jsonify(obj), 400)

    if len(email) == 0:
        obj = {"message": "Field email is missing."}
        return make_response(jsonify(obj), 400)

    if len(password) == 0:
        obj = {"message": "Field password is missing."}
        return make_response(jsonify(obj), 400)

    if not checkEmail(email):
        obj = {"message": "Invalid email."}
        return make_response(jsonify(obj), 400)

    if not checkPassword(password):
        obj = {"message": "Invalid password."}
        return make_response(jsonify(obj), 400)

    emailExists = User.query.filter(User.email == email).first()
    if emailExists is not None:
        obj = {"message": "Email already exists."}
        return make_response(jsonify(obj), 400)

    user = User(email=email, password=password, forename=forename, surname=surname)
    db.session.add(user)
    db.session.commit()

    userRole = UserRole(userId=user.id, roleId=3)
    db.session.add(userRole)
    db.session.commit()

    return Response("Registration customer successful!", status=200);


@app.route("/register_courier", methods=["POST"])
def registerCourier():

    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    if len(forename) == 0:
        obj = {"message": "Field forename is missing."}
        return make_response(jsonify(obj), 400)

    if len(surname) == 0:
        obj = {"message": "Field surname is missing."}
        return make_response(jsonify(obj), 400)

    if len(email) == 0:
        obj = {"message": "Field email is missing."}
        return make_response(jsonify(obj), 400)

    if len(password) == 0:
        obj = {"message": "Field password is missing."}
        return make_response(jsonify(obj), 400)

    if not checkEmail(email):
        obj = {"message": "Invalid email."}
        return make_response(jsonify(obj), 400)

    if not checkPassword(password):
        obj = {"message": "Invalid password."}
        return make_response(jsonify(obj), 400)

    emailExists = User.query.filter(User.email == email).first()
    if emailExists is not None:
        obj = {"message": "Email already exists."}
        return make_response(jsonify(obj), 400)

    user = User(email=email, password=password, forename=forename, surname=surname)
    db.session.add(user)
    db.session.commit()

    userRole = UserRole(userId=user.id, roleId=4)
    db.session.add(userRole)
    db.session.commit()

    return Response("Registration courier successful!", status=200)


jwt = JWTManager(app)


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if len(email) == 0:
        obj = {"message": "Field email is missing."}
        return make_response(jsonify(obj), 400)

    if len(password) == 0:
        obj = {"message": "Field password is missing."}
        return make_response(jsonify(obj), 400)

    if not checkEmail(email):
        obj = {"message": "Invalid email."}
        return make_response(jsonify(obj), 400)

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        obj = {"message": "Invalid credentials."}
        return make_response(jsonify(obj), 400)

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles],
        "email": user.email,
        "id": user.id
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    if accessToken is None or refreshToken is None:
        obj = {"message": "Token creation failed."}
        return make_response(jsonify(obj), 400)

    return jsonify(accessToken=accessToken, refreshToken=refreshToken)


@app.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!"


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"],
        "email": refreshClaims["email"],
        "id": refreshClaims["id"]
    }

    token = create_access_token(identity=identity, additional_claims=additionalClaims)
    if token is None:
        obj = {"message": "Refreshing token failed."}
        return make_response(jsonify(obj), 400)

    obj = {'accessToken': token}
    return make_response(obj, 200)


@app.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    identity = get_jwt_identity()

    if identity is None:
        obj = {"msg": "Missing Authorization Header"}
        return make_response(jsonify(obj), 401)

    # email = request.json.get("email", "")
    # if len(email) == 0:
    #     obj = {"message": "Field email is missing."}
    #     return make_response(jsonify(obj), 400)
    #
    # if not checkEmail(email):
    #     obj = {"message": "Invalid email."}
    #     return make_response(jsonify(obj), 400)

    userDoesNotExist = User.query.filter(User.email == identity).first()
    if userDoesNotExist is None:
        obj = {"message": "Unknown user."}
        return make_response(jsonify(obj), 400)

    User.query.filter(User.email == identity).delete()
    db.session.commit()

    return Response(status=200)


@app.route("/", methods=["GET"])
def index():
    return "Hello from authentication"


if __name__ == "__main__":
    db.init_app(app)
    app.run(debug=True, host="0.0.0.0", port=5004)
