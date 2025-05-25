  
import os
from flask_admin import Admin
from .models import db, User, Product
from flask_admin.contrib.sqla import ModelView

class UserView(ModelView):
    column_list = ('id', 'email', 'password', 'role')

class ProductView(ModelView):
    column_list = ('id', 'name', 'description', 'price', 'image_url')


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    
    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(UserView(User, db.session))
    admin.add_view(ProductView(Product, db.session))
    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))