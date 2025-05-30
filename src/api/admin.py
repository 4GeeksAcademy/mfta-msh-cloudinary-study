  
import os
from flask_admin import Admin
from .models import db, User, Product, ProductImage
from flask_admin.contrib.sqla import ModelView

class UserView(ModelView):
    column_list = ('id', 'email', 'password', 'role', 'picture_url', 'picture_public_id')

class ProductView(ModelView):
    column_list = ('id', 'name', 'description', 'price', 'images')

class ProductImageView(ModelView):
    column_list = ('id', 'product_id', 'image_url', 'public_id')

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    
    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(UserView(User, db.session))
    admin.add_view(ProductView(Product, db.session))
    admin.add_view(ProductImageView(ProductImage, db.session))
    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))