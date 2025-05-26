"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, create_access_token
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from api.utils import APIException, generate_sitemap
from api.models import db, User, Product
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands

# from models import Person

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False
bcrypt = Bcrypt(app)

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

# Cloudinary configuration
# Make sure to set your Cloudinary credentials in the environment variables      
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "your_cloud_name"),
    api_key = os.getenv("CLOUDINARY_API_KEY", "your_api_key"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "your_api_secret"),
    secure=True
)


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
    Body example:
    {
        "email": "user1@email.com",
        "password": "user1password",
        "role": "user"  # optional, defaults to "user"
    }
    """

    body = request.get_json()
    if not body or "email" not in body or "password" not in body:
        return jsonify({"error": "Missing email or password"}), 400
    email = body["email"]
    password = body["password"]
    role = body.get("role", "user")

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"error": "User already exists"}), 400
    
    if role not in ["user", "admin"]:
        return jsonify({"error": "Invalid role"}), 400
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully", "user": new_user.serialize() }), 201


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
    Body example:
    {
        "name": "Product Name",
        "description": "Product Description",
        "price": 100.00,
        "image": "image_file"  # file upload
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

    # Check if the image file is present
    if 'image' not in request.files:
        return jsonify({"error": "Missing image file"}), 400

    # Get the image file from the request
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Validate image file type
    if not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        return jsonify({"error": "Invalid image format"}), 400
    
    # Validate image file size (max 3MB)
    if image_file.content_length > 3 * 1024 * 1024:
        return jsonify({"error": "Image file too large, must be less than 3MB"}), 400
    
    try:
        # First, create the product without the image
        # This allows us to handle the image upload separately (e.g., if the product creation fails, we don't want to leave an image in Cloudinary)
        new_product = Product(name=name, description=description, price=price)
        db.session.add(new_product)
        
        # Then upload image to Cloudinary
        upload_result = cloudinary.uploader.upload(image_file, folder="/Practice-Projects/cloudinary-study-py")
        print(upload_result)
        image_url = upload_result['secure_url']
        image_public_id = upload_result['public_id']

        # Update the product with the image URL
        new_product.image_url = image_url
        new_product.image_public_id = image_public_id
        db.session.commit()
        
        return jsonify({"message": "Product created successfully", "product": new_product.serialize()}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to upload product: {str(e)}"}), 500
    

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
