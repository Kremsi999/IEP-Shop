from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import db, Reserved, Order, ProductCategory, Product, Category
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, db)

if __name__ == "__main__":

    migrationFinished = False
    while not migrationFinished:
        try:
            if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
                create_database(application.config["SQLALCHEMY_DATABASE_URI"])

            db.init_app(application)

            with application.app_context() as context:
                init()
                migrate(message="Shop migrations")
                upgrade()

                db.session.commit()
                done = True

        except Exception as exception:
            print(exception)
