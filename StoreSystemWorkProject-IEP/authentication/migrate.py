from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import db, Role, UserRole, User
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, db)

if __name__ == '__main__':
    migrationFinished = False
    while not migrationFinished:
        try:
            if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
                create_database(application.config["SQLALCHEMY_DATABASE_URI"])

            db.init_app(application);

            with application.app_context() as context:
                init()
                migrate(message="Authentication migration")
                upgrade()

                adminRole = Role(name="administrator")
                ownerRole = Role(name='owner')
                customer = Role(name="customer")
                courier = Role(name='courier')

                db.session.add(adminRole)
                db.session.add(ownerRole)
                db.session.add(customer)
                db.session.add(courier)
                db.session.commit()

                admin = User(
                    email="admin@admin.com",
                    password="1",
                    forename="admin",
                    surname="admin"
                )

                db.session.add(admin)
                db.session.commit()

                owner = User(
                    forename= "Scrooge",
                    surname= "McDuck",
                    email= "onlymoney@gmail.com",
                    password= "evenmoremoney"
                )

                db.session.add(owner)
                db.session.commit()

                userRole = UserRole(
                    userId=admin.id,
                    roleId=adminRole.id
                )

                ownerRoleAdded = UserRole(
                    userId=owner.id,
                    roleId=ownerRole.id
                )

                db.session.add(ownerRoleAdded)
                db.session.commit()

                db.session.add(userRole)
                db.session.commit()
                migrationFinished = True

        except Exception as exception:
            print(exception)
