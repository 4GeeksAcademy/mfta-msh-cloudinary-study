"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, create_access_token
from flask_cors import CORS
# Relevant for this Study Project ##############################################################################################
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
################################################################################################################################

from api.utils import APIException, generate_sitemap
from api.models import db, User, Product, ProductImage
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False
bcrypt = Bcrypt(app)
# Enable CORS for all routes
CORS(app)

# database condiguration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

# Relevant for this Study Project ##############################################################################################
# Cloudinary configuration
# Make sure to set your Cloudinary credentials in the environment variables      
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "your_cloud_name"),
    api_key = os.getenv("CLOUDINARY_API_KEY", "your_api_key"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "your_api_secret"),
    secure=True
)
################################################################################################################################

# add the admin
setup_admin(app)

# add the admin
setup_commands(app)

# Add all endpoints form the API with a "api" prefix
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# any other endpoint will try to serve it like a static file
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response


# User register endpoint
@app.route('/register', methods=['POST'])
def register_user():
    """
    Form data example:
    email= "user@email.com"
    password= "userpassword"
    role= "user"  # Optional, default is "user"
    image= <image file>  # Optional, can upload an image file
    """
    form = request.form
    if not form or "email" not in form or "password" not in form:
        return jsonify({"error": "Missing email or password"}), 400
    email = form["email"]
    password = form["password"]
    role = form.get("role", "user")  # Default role is "user"
    if role not in ["user", "admin"]:
        return jsonify({"error": "Invalid role, must be 'user' or 'admin'"}), 400
    # Check if the user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 400
    # Validate password length
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400
    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Check if the image file is present
    if 'image' in request.files:
        # Check if the image file is valid
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        # Validate image file type
        if not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({"error": "Invalid image format"}), 400
        # Validate image file size (max 2MB)
        if image_file.content_length > 2 * 1024 * 1024:
            return jsonify({"error": "Image file too large, must be less than 2MB"}), 400

        try:
        # Relevant for this Study Project ##############################################################################################
            # Upload one image to Cloudinary
            upload_result = cloudinary.uploader.upload(image_file, folder="/Practice-Projects/cloudinary-study-py")
            image_url = upload_result['secure_url']
            image_public_id = upload_result['public_id']
        ################################################################################################################################
        except Exception as e:
            return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500
    else:
        image_url = "https://res.cloudinary.com/dbiyjz0g3/image/upload/v1748279029/Practice-Projects/cloudinary-study-py/avatar_f6r5cf.jpg"
        image_public_id = None
    
    # Create the new user
    new_user = User(email=email, password=hashed_password, role=role, picture_url=image_url, picture_public_id=image_public_id)
    try:
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to register user: {str(e)}"}), 500
    


# User login endpoint with JWT
@app.route('/login', methods=['POST'])
def login_user():
    """
    Body example:
    {
        "email": "user1@email.com",
        "password": "user1password"
    }
    """
    body = request.get_json()
    if not body or "email" not in body or "password" not in body:
        return jsonify({"error": "Missing email or password"}), 400

    email = body["email"]
    password = body["password"]

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "user": user.serialize()}), 200


# Product create endpoint
# Images: receive an image file and upload it to Cloudinary
@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    """
    Body example (multipart/form-data):
    {
        "name": "Product Name",
        "description": "Product Description",
        "price": 100.00,
        "images": list of image files (optional, can upload up to 5 images)
    }
    """
    # Check if the user is an admin
    current_user = get_jwt_identity()
    user = User.query.get(int(current_user))
    if not user or user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    # Check if the request contains form data
    body = request.form
    if not body or "name" not in body or "description" not in body or "price" not in body:
        return jsonify({"error": "Missing product data"}), 400
    
    # Check if a product with the same name already exists
    existing_product = Product.query.filter_by(name=body["name"]).first()
    if existing_product:
        return jsonify({"error": "Product with this name already exists"}), 400
    
    # Validate price
    try:
        price = float(body["price"])
        if price <= 0:
            return jsonify({"error": "Price must be a positive number"}), 400
    except ValueError:
        return jsonify({"error": "Invalid price format"}), 400

    # Extract product data from the form
    name = body["name"]
    description = body["description"]
    price = float(body["price"])

    images_urls = []

    # Check if images are provided
    if 'images' not in request.files or len(request.files.getlist('images')) == 0:
        images_urls = [
            {
                "url": "https://res.cloudinary.com/dbiyjz0g3/image/upload/v1748280952/Practice-Projects/cloudinary-study-py/no_image_available_vh4dpj.png",
                "public_id": None
            }
        ]
    else:
        image_files = request.files.getlist('images')
        if len(image_files) > 5:
            return jsonify({"error": "You can upload a maximum of 5 images"}), 400
        
        for image_file in image_files:
            if image_file.filename == '':
                return jsonify({"error": "No selected file"}), 400
            
            # Validate image file type
            if not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return jsonify({"error": "Invalid image format"}), 400
            
            # Validate image file size (max 3MB)
            if image_file.content_length > 3 * 1024 * 1024:
                return jsonify({"error": "Image file too large, must be less than 3MB"}), 400
            
            try:
                # Upload the image to Cloudinary
                upload_result = cloudinary.uploader.upload(image_file, folder="/Practice-Projects/cloudinary-study-py")
                images_urls.append({
                    "url": upload_result['secure_url'],
                    "public_id": upload_result['public_id']
                })
            except Exception as e:
                return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500


    # Create a new product instance
    new_product = Product(name=name, description=description, price=price)
    try:
        db.session.add(new_product)
        db.session.commit() # After committing the product, we can get its ID to associate images
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create product: {str(e)}"}), 500

    # Save the images to the database
    for image_data in images_urls:
        new_image = ProductImage(
            product_id=new_product.id,
            url=image_data["url"],
            public_id=image_data["public_id"]
        )
        db.session.add(new_image)
    try:
        db.session.commit()
        return jsonify({"message": "Product created successfully", "product": new_product.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create product: {str(e)}"}), 500
    
    

# Product update endpoint
@app.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """
    Body example (multipart/form-data):
    {
        "name": "Updated Product Name",
        "description": "Updated Product Description",
        "price": 150.00,
        "image_files_to_add": list of image files (optional, can upload up to 5 new images),
        "image_ids_to_delete": list of image IDs to delete (optional)
    }
    All fields are optional, but at least one must be provided.
    """
    # Check if the user is an admin
    current_user = get_jwt_identity()
    user = User.query.get(int(current_user))
    if not user or user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    body = request.form
    if not body or ("name" not in body and "description" not in body and "price" not in body and 'image' not in request.files):
        return jsonify({"error": "Missing product data"}), 400
    
    # Update product fields if provided
    if "name" in body:
        # Check if a product with the same name already exists
        existing_product = Product.query.filter_by(name=body["name"]).first()
        if existing_product and existing_product.id != product_id:
            return jsonify({"error": "Product with this name already exists"}), 400
        # Update the product name
        product.name = body["name"]
    
    if "description" in body:
        product.description = body["description"]
    
    if "price" in body:
        try:
            price = float(body["price"])
            if price <= 0:
                return jsonify({"error": "Price must be a positive number"}), 400
            product.price = price
        except ValueError:
            return jsonify({"error": "Invalid price format"}), 400

    # Handle image updates
    image_files = request.files.getlist('image_files_to_add')
    image_ids_to_delete = request.form.getlist('image_ids_to_delete')
    if len(image_files) > 5:
        return jsonify({"error": "You can upload a maximum of 5 images"}), 400
    if product.images and (len(product.images) + len(image_files) - len(image_ids_to_delete)) > 5:
        return jsonify({"error": "Total images cannot exceed 5"}), 400
    
    # Delete specified images
    for image_id in image_ids_to_delete:
        image = ProductImage.query.get(image_id)
        if not image or image.product_id != product_id:
            return jsonify({"error": f"Image with ID {image_id} not found for this product"}), 404
        try:
            db.session.delete(image)
            db.session.commit()
            # Delete the image from Cloudinary if it exists
            if image.public_id:
                cloudinary.uploader.destroy(image.public_id)
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete image: {str(e)}"}), 500
        
    # Add new images
    images_urls = []
    if image_files:
        for image_file in image_files:
            if image_file.filename == '':
                return jsonify({"error": "No selected file"}), 400
            
            # Validate image file type
            if not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return jsonify({"error": "Invalid image format"}), 400
            
            # Validate image file size (max 3MB)
            if image_file.content_length > 3 * 1024 * 1024:
                return jsonify({"error": "Image file too large, must be less than 3MB"}), 400
            
            try:
                # Upload the image to Cloudinary
                upload_result = cloudinary.uploader.upload(image_file, folder="/Practice-Projects/cloudinary-study-py")
                images_urls.append({
                    "url": upload_result['secure_url'],
                    "public_id": upload_result['public_id']
                })
            except Exception as e:
                return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500

        # Save the new images to the database
        for image_data in images_urls:
            new_image = ProductImage(
                product_id=product.id,
                url=image_data["url"],
                public_id=image_data["public_id"]
            )
            db.session.add(new_image)
    try:
        db.session.commit()
        return jsonify({"message": "Product updated successfully", "product": product.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update product: {str(e)}"}), 500

    
    

# Product delete endpoint
@app.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """
    Deletes a product by ID
    """
    # Check if the user is an admin
    current_user = get_jwt_identity()
    user = User.query.get(int(current_user))
    if not user or user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    try:
        db.session.delete(product)
        db.session.commit()

        # Delete the images from Cloudinary if it exists
        if product.images:
            for image in product.images:
                if image.public_id:
                    cloudinary.uploader.destroy(image.public_id)
                    
        return jsonify({"message": "Product deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete product: {str(e)}"}), 500

############################################################################################# 

# Product list endpoint
@app.route('/products', methods=['GET'])
@jwt_required()
def list_products():
    """
    Returns a list of all products
    """
    products = Product.query.all()
    return jsonify({"products": [product.serialize() for product in products]}), 200


# Product detail endpoint
@app.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """
    Returns the details of a specific product by ID
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product.serialize()}), 200
    

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
