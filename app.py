import joblib
import re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, BooleanField, TextAreaField, FloatField, SubmitField
from wtforms.validators import DataRequired
import pymysql
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, BooleanField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from io import BytesIO
from PIL import Image
import base64
import io
from flask_cors import CORS




pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app ,origins=['http://localhost:3000'])
app.config['SECRET_KEY'] = 'mysecretkey'

login_manager = LoginManager(app)
login_manager.login_view = 'login'


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/eatlytic'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/products'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

class Product(db.Model):
    __tablename__ = 'products' 

    id = db.Column(db.Integer, primary_key=True) 
    title = db.Column(db.String(255), nullable=False) 
    description = db.Column(db.Text)  
    price = db.Column(db.Numeric(10, 2), nullable=False)  
    category = db.Column(db.String(100))  
    size = db.Column(db.String(50)) 
    color = db.Column(db.String(50))  
    availability = db.Column(db.String(50)) 
    top_rated = db.Column(db.Boolean, default=False) 
    product_type = db.Column(db.String(100))  
    brand = db.Column(db.String(100))  
    discount = db.Column(db.Numeric(5, 2)) 
    offer = db.Column(db.String(100)) 
    views = db.Column(db.Integer, default=0) 
    reviews = db.Column(db.Integer, default=0) 
    calories = db.Column(db.Numeric(10, 2))  
    protein = db.Column(db.Numeric(10, 2)) 
    carbohydrates = db.Column(db.Numeric(10, 2))
    fat = db.Column(db.Numeric(10, 2))  
    fiber = db.Column(db.Numeric(10, 2)) 
    sugars = db.Column(db.Numeric(10, 2)) 
    sodium = db.Column(db.Numeric(10, 2)) 
    cholesterol = db.Column(db.Numeric(10, 2)) 
    meal_type = db.Column(db.String(100))
    image = db.Column(db.LargeBinary) 

class ProductForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = DecimalField('Price', validators=[DataRequired()])
    category = SelectField('Category', choices=[('hot sale', 'Hot Sale'), ('best selling', 'Best Selling')])
    size = StringField('Size')
    color = StringField('Color')
    availability = StringField('Availability')
    top_rated = BooleanField('Top Rated')
    product_type = StringField('Product Type')
    brand = StringField('Brand')
    discount = DecimalField('Discount')
    offer = StringField('Offer')
    views = DecimalField('Views')
    reviews = DecimalField('Reviews')
    calories = DecimalField('Calories')
    protein = DecimalField('Protein')
    carbohydrates = DecimalField('Carbohydrates')
    fat = DecimalField('Fat')
    fiber = DecimalField('Fiber')
    sugars = DecimalField('Sugars')
    sodium = DecimalField('Sodium')
    cholesterol = DecimalField('Cholesterol')
    meal_type = StringField('Meal Type')
    image = FileField('Product Image') 

class PredictionForm(FlaskForm):
    feature1 = FloatField('Feature 1', validators=[DataRequired()])
    feature2 = FloatField('Feature 2', validators=[DataRequired()])
    submit = SubmitField('Get Prediction')

model = joblib.load('./best_model.pkl')

class QueryForm(FlaskForm):
    query = StringField('Enter your query', validators=[DataRequired()])
    submit = SubmitField('Search Foods')

def extract_features_from_query(query):
    filters = {}

    if re.search(r'low\s*calorie', query, re.IGNORECASE):
        filters['calories'] = 'low'
    elif re.search(r'high\s*calorie', query, re.IGNORECASE):
        filters['calories'] = 'high'
    calories_match = re.search(r'calories\s*(<|<=|>|>=|=)\s*(\d+)', query, re.IGNORECASE)
    if calories_match:
        filters['calories_value'] = {
            'operator': calories_match.group(1),
            'value': int(calories_match.group(2))
        }

    if re.search(r'high\s*protein', query, re.IGNORECASE):
        filters['protein'] = 'high'
    elif re.search(r'low\s*protein', query, re.IGNORECASE):
        filters['protein'] = 'low'
    protein_match = re.search(r'protein\s*(<|<=|>|>=|=)\s*(\d+)', query, re.IGNORECASE)
    if protein_match:
        filters['protein_value'] = {
            'operator': protein_match.group(1),
            'value': int(protein_match.group(2))
        }


    if re.search(r'low\s*fiber', query, re.IGNORECASE):
        filters['fiber'] = 'low'
    fiber_match = re.search(r'fiber\s*(<|<=|>|>=|=)\s*(\d+)', query, re.IGNORECASE)
    if fiber_match:
        filters['fiber_value'] = {
            'operator': fiber_match.group(1),
            'value': int(fiber_match.group(2))
        }

    if re.search(r'low\s*sugars', query, re.IGNORECASE):
        filters['sugars'] = 'low'
    elif re.search(r'high\s*sugars', query, re.IGNORECASE):
        filters['sugars'] = 'high'
    sugars_match = re.search(r'sugars\s*(<|<=|>|>=|=)\s*(\d+)', query, re.IGNORECASE)
    if sugars_match:
        filters['sugars_value'] = {
            'operator': sugars_match.group(1),
            'value': int(sugars_match.group(2))
        }

    return filters

def get_filtered_foods(filters):
    query = db.session.query(Product)

    if 'calories' in filters:
        if filters['calories'] == 'low':
            query = query.filter(Product.calories < 100) 
        elif filters['calories'] == 'high':
            query = query.filter(Product.calories > 200) 

    if 'calories_value' in filters:
        operator = filters['calories_value']['operator']
        value = filters['calories_value']['value']
        if operator == '<':
            query = query.filter(Product.calories < value)
        elif operator == '<=':
            query = query.filter(Product.calories <= value)
        elif operator == '>':
            query = query.filter(Product.calories > value)
        elif operator == '>=':
            query = query.filter(Product.calories >= value)
        elif operator == '=':
            query = query.filter(Product.calories == value)


    if 'protein' in filters:
        if filters['protein'] == 'high':
            query = query.filter(Product.protein > 10)
        elif filters['protein'] == 'low':
            query = query.filter(Product.protein < 5)

    if 'protein_value' in filters:
        operator = filters['protein_value']['operator']
        value = filters['protein_value']['value']
        if operator == '<':
            query = query.filter(Product.protein < value)
        elif operator == '<=':
            query = query.filter(Product.protein <= value)
        elif operator == '>':
            query = query.filter(Product.protein > value)
        elif operator == '>=':
            query = query.filter(Product.protein >= value)
        elif operator == '=':
            query = query.filter(Product.protein == value)

    if 'sugars' in filters:
        if filters['sugars'] == 'low':
            query = query.filter(Product.sugars < 10) 
        elif filters['sugars'] == 'high':
            query = query.filter(Product.sugars > 20)

    if 'sugars_value' in filters:
        operator = filters['sugars_value']['operator']
        value = filters['sugars_value']['value']
        if operator == '<':
            query = query.filter(Product.sugars < value)
        elif operator == '<=':
            query = query.filter(Product.sugars <= value)
        elif operator == '>':
            query = query.filter(Product.sugars > value)
        elif operator == '>=':
            query = query.filter(Product.sugars >= value)
        elif operator == '=':
            query = query.filter(Product.sugars == value)


    filtered_foods = query.all()
    return filtered_foods
@app.route('/', methods=['GET', 'POST'])
def index():
    form = QueryForm()

    if form.validate_on_submit():
        user_query = form.query.data 
        filters = extract_features_from_query(user_query)  


        filtered_foods = get_filtered_foods(filters)

        return render_template('result.html', filtered_foods=filtered_foods)

    return render_template('index.html', form=form)



import base64

def serialize_product(product):
    # Convert image (if exists) from bytes to base64 string
    image_base64 = None
    if product.image:
        image_base64 = base64.b64encode(product.image).decode('utf-8')  # Convert bytes to base64 string

    return {
        'id': product.id,
        'title': product.title,
        'description': product.description,
        'price': str(product.price),
        'category': product.category,
        'size': product.size,
        'color': product.color,
        'availability': product.availability,
        'top_rated': product.top_rated,
        'product_type': product.product_type,
        'brand': product.brand,
        'discount': str(product.discount),
        'offer': product.offer,
        'views': product.views,
        'reviews': product.reviews,
        'calories': str(product.calories),
        'protein': str(product.protein),
        'carbohydrates': str(product.carbohydrates),
        'fat': str(product.fat),
        'fiber': str(product.fiber),
        'sugars': str(product.sugars),
        'sodium': str(product.sodium),
        'cholesterol': str(product.cholesterol),
        'meal_type': product.meal_type,
        'image': image_base64 
    }

   


@app.route('/api/query', methods=['GET'])
def api_query():
    user_query = request.args.get('query')
    
    if user_query:
        filters = extract_features_from_query(user_query)
        filtered_foods = get_filtered_foods(filters)


        filtered_foods_data = [serialize_product(food) for food in filtered_foods]

        return jsonify(filtered_foods_data) 
    else:
        return jsonify({'error': 'Query parameter is required'}), 400


@app.route('/result')
def result():
    return render_template('result.html')




@app.route('/login', methods=['GET', 'POST'])
def login():

    admin_username = "admin"
    admin_password = "adminpassword" 

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        if username == admin_username and password == admin_password:
            user = User(1) 
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

def encode_image(image_binary):

    return base64.b64encode(image_binary).decode('utf-8')


@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.all()  

    for product in products:
        if product.image:
            product.image_base64 = encode_image(product.image) 
        else:
            product.image_base64 = None
    return render_template('dashboard.html', products=products)


def compress_image(image_file):

    img = Image.open(image_file)
    

    img = img.resize((800, 800))  
    
  
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=50) 
    img_io.seek(0)  
    
    return img_io.getvalue() 

@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    form = ProductForm()

    if request.method == 'POST' and form.validate_on_submit():

        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):

                compressed_image = compress_image(image)

       
                new_product = Product(
                    title=form.title.data,
                    description=form.description.data,
                    price=form.price.data,
                    category=form.category.data,
                    size=form.size.data,
                    color=form.color.data,
                    availability=form.availability.data,
                    top_rated=form.top_rated.data,
                    product_type=form.product_type.data,
                    brand=form.brand.data,
                    discount=form.discount.data,
                    offer=form.offer.data,
                    views=form.views.data,
                    reviews=form.reviews.data,
                    calories=form.calories.data,
                    protein=form.protein.data,
                    carbohydrates=form.carbohydrates.data,
                    fat=form.fat.data,
                    fiber=form.fiber.data,
                    sugars=form.sugars.data,
                    sodium=form.sodium.data,
                    cholesterol=form.cholesterol.data,
                    meal_type=form.meal_type.data,
                    image=compressed_image 
                )

                db.session.add(new_product)
                db.session.commit()

                flash('Product added successfully with compressed image!', 'success')
                return redirect(url_for('products'))

        flash('Invalid image file type. Please upload a valid image file (png, jpg, jpeg, gif).', 'danger')

    return render_template('add_products.html', form=form)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



    



@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get(id)  
    form = ProductForm(obj=product) 
    if request.method == 'POST' and form.validate_on_submit():

        if 'image' in request.files and request.files['image']:
            image = request.files['image']
            if image and allowed_file(image.filename):

                compressed_image = compress_image(image)
                product.image = compressed_image 

        product.title = form.title.data
        product.description = form.description.data
        product.price = form.price.data
        product.category = form.category.data
        product.size = form.size.data
        product.color = form.color.data
        product.availability = form.availability.data
        product.top_rated = form.top_rated.data
        product.product_type = form.product_type.data
        product.brand = form.brand.data
        product.discount = form.discount.data
        product.offer = form.offer.data
        product.views = form.views.data
        product.reviews = form.reviews.data
        product.calories = form.calories.data
        product.protein = form.protein.data
        product.carbohydrates = form.carbohydrates.data
        product.fat = form.fat.data
        product.fiber = form.fiber.data
        product.sugars = form.sugars.data
        product.sodium = form.sodium.data
        product.cholesterol = form.cholesterol.data
        product.meal_type = form.meal_type.data

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_product.html', form=form, product=product)


@app.route('/delete_product/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_product(id):
    product = Product.query.get(id)
    db.session.delete(product)  
    db.session.commit()  
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = Product.query.all()
    products_list = []

    for product in products:
        product_data = {
            'id': product.id,
            'title': product.title,
            'price': str(product.price), 
            'category': product.category,
            'image' : "test"
        }

        if product.image:
            product_data['image'] = encode_image(product.image)
        else:
            product_data['image'] = None

        products_list.append(product_data)

    return jsonify(products_list)







if __name__ == '__main__':
    app.run(debug=True)
