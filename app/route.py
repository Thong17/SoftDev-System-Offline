from app import app, bcrypt, db, login_manager, c, upload, delete_photo
from app import tblUser, tblBrand, tblCategory, tblProperty, tblProduct, tblColor, tblPhoto, tblValue
from app import LoginForm, RegisterForm, CategoryForm, BrandForm
from app import CategorySchema, ProductSchema, ColorSchema, BrandSchema
from flask import render_template, redirect, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from uuid import uuid4
import json, simplejson
from datetime import datetime, timedelta, date
from sqlalchemy import func
from decimal import Decimal


@login_manager.user_loader
def load_user(id):
    return tblUser.query.get(id)


@app.route('/')
@login_required
def index():
    return render_template('views/index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        msg = {
            'username': [],
            'password': [],
            'redirect': ''
        }
        if form.validate_on_submit():
            username = request.form['username']
            password = request.form['password']
            try:
                user = tblUser.query.filter_by(username=username).first()
                while user is not None:
                    isMatch = bcrypt.check_password_hash(
                        user.password, password)
                    if isMatch is True:
                        login_user(user)
                        msg['redirect'] = '/'
                        return jsonify(msg)
                    msg['password'].append('Password does not match')
                    return jsonify(msg)
                msg['username'].append('Username does not exist')
                return jsonify(msg)
            except:
                msg['username'].append('Connection is not available')
                return jsonify(msg)
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                msg[fieldName].append(err)
        return jsonify(msg)
    return render_template('views/login.html', form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            username = request.form['username']
            gender = request.form['gender']
            birthdate = form.birthdate.data
            email = request.form['email']
            password = request.form['password']

            #Generate unique Id
            id = str(uuid4())
            profile_id = str(uuid4())

            #Encrypt the password field
            hashed_password = bcrypt.generate_password_hash(
                password).decode('utf-8')

            #User to register
            requestedUser = tblUser(id=id, firstname=firstname, lastname=lastname, username=username, gender=gender,
                                    birthdate=birthdate, email=email, password=hashed_password, publicId=str(uuid4()))

            try:
                db.session.add(requestedUser)
                db.session.commit()

                return redirect('/')
            except SQLAlchemyError as error:
                print(str(error))
                db.session.rollback()
                return 'Register failed'
    return render_template('views/register.html', form=form)


@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect('/login')


@app.route('/setting')
@login_required
def setting():
    return render_template('views/setting.html')


@app.route('/custome', methods=['POST', 'GET'])
@login_required
def custome():
    if request.method == 'POST':
        categories = tblCategory.query.all()
        category_schema = CategorySchema()
        category = category_schema.dump(categories, many=True)

        brands = tblBrand.query.all()
        brand_schema = BrandSchema()
        brand = brand_schema.dump(brands, many=True)

        result = {}
        result['categories'] = category
        result['brands'] = brand

        return jsonify(result)
    return render_template('views/custome.html')


@app.route('/category', methods=['POST', 'GET'])
@login_required
def categories():
    form = CategoryForm()
    categories = tblCategory.query.all()
    total = len(categories)
    today = []

    for item in categories:
        if datetime.now().date() == item.createdOn.date():
            today.append(item)
    if request.method == 'POST':
        msg = {
            'category': [],
            'redirect': '',
            'name': '',
            'id': '',
            'total': 0,
            'today': 0
        }
        if form.validate_on_submit():
            category = request.form['category']
            description = request.form['description']
            id = str(uuid4())
            Modal = tblCategory(id=id, category=category,
                                description=description, createdBy=current_user.id)
            msg['name'] = category
            msg['id'] = id
            try:
                db.session.add(Modal)
                db.session.commit()
                total += 1
                today = len(today) + 1
                msg['redirect'] = '/category'
                msg['total'] = total
                msg['today'] = today
                return jsonify(msg)
            except:
                return 'Failed'
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                msg[fieldName].append(err)
        return jsonify(msg)
    return render_template('views/category.html', form=form, categories=categories, today=today, total=total)


@app.route('/category/<id>', methods=['POST'])
def category(id):
    if request.form['data']:
        id = request.form['data']
        category = tblCategory.query.get(id)
        json = CategorySchema()
        result = json.dump(category)
    return jsonify(result)


@app.route('/category/property', methods=['POST'])
@login_required
def add_property():
    categoryId = request.form['categoryId']
    _property = request.form['property']
    _type = request.form['type']
    description = request.form['description']
    id = str(uuid4())

    Modal = tblProperty(id=id, property=_property, type=_type,
                        description=description, categoryId=categoryId, createdBy=current_user.id)

    db.session.add(Modal)
    db.session.commit()
    return jsonify({'id': id, 'property': _property, 'type': _type, 'description': description, 'msg': ''})

@app.route('/property/remove/<id>', methods=['POST'])
@login_required
def remove_property(id):
    if request.form['data']:
        id = request.form['data']
        try:
            _property = tblProperty.query.get(id)
            db.session.delete(_property)
            db.session.commit()
            return jsonify({'msg': 'Property deleted'})
        except:
            return 'Failded'

@app.route('/property/update/<id>', methods=['POST'])
def update_property(id):
    _property = tblProperty.query.get(id)

    new_property = request.form['property']
    new_type = request.form['type']
    new_description = request.form['description']

    _property.property = new_property
    _property.type = new_type
    _property.description = new_description

    try:
        db.session.commit()
        return jsonify({'id': id, 'property': new_property, 'type': new_type, 'description': new_description})
    except:
        return jsonify({'msg': 'Failed'})

@app.route('/category/remove/<id>', methods=['POST'])
def remove_category(id):
    category = tblCategory.query.get(id)
    try: 
        db.session.delete(category)
        db.session.commit()
        categories = tblCategory.query.all()
        today = []
        for item in categories:
            if datetime.now().date() == item.createdOn.date():
                today.append(item)
        return jsonify({'msg': 'Success', 'today': len(today), 'total': len(categories)})
    except:
        return jsonify({'msg': 'Failed'})

@app.route('/category/update/<id>', methods=['POST'])
def udpate_category(id):
    category = tblCategory.query.get(id)
    
    try:
        category.category = request.form['data']
        db.session.commit()
        return jsonify({'category': request.form['data'], 'msg': 'Success'})
    except: 
        return jsonify({'msg': 'Failed'})

@app.route('/brand', methods=['POST', 'GET'])
@login_required
def brands():
    brands = tblBrand.query.all()
    categories = tblCategory.query.with_entities(tblCategory.id, tblCategory.category).all()
    form = BrandForm()
    if request.method == 'POST':
        msg = {
            'brand': [],
            'redirect': '',
            'name': '',
            'id': ''
        }
        if form.validate_on_submit():
            brand = request.form['brand']
            description = request.form['description']
            id = str(uuid4())
            Modal = tblBrand(id=id, brand=brand, description=description, createdBy=current_user.id)
            msg['name'] = brand
            msg['id'] = id
            try:
                db.session.add(Modal)
                db.session.commit()
                msg['redirect'] = '/brand'
                return jsonify(msg)
            except:
                return 'Failed'
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                msg[fieldName].append(err)
        return jsonify(msg)
    return render_template('views/product.html', brands=brands, form=form, categories=categories)

@app.route('/brand/remove/<id>', methods=['POST'])
def remove_brand(id):
    brand = tblBrand.query.get(id)
    try: 
        db.session.delete(brand)
        db.session.commit()
        return jsonify({'msg': 'Success'})
    except:
        return jsonify({'msg': 'Failed'})

@app.route('/brand/update/<id>', methods=['POST'])
def udpate_brand(id):
    brand = tblBrand.query.get(id)
    try:
        brand.brand = request.form['data']
        db.session.commit()
        return jsonify({'brand': request.form['data'], 'msg': 'Success'})
    except: 
        return jsonify({'msg': 'Failed'})

@app.route('/theme/change', methods=['POST'])
def theme():
    theme = request.form['data']
    user = tblUser.query.get(current_user.id)
    user.theme = theme
    db.session.commit()
    return jsonify({'theme': theme})

@app.route('/product/add', methods=['POST'])
def add_product():
    product = request.form['product']
    price = request.form['price']
    cost = request.form['cost']
    category = request.form['category']
    currency = request.form['currency']
    quantity = request.form['quantity']
    description = request.form['details']
    brand = request.form['brand']

    id = str(uuid4())

    Model = tblProduct(id=id, product=product, price=price, cost=cost, quantity=quantity, currency=currency, description=description, createdBy=current_user.id, categoryId=category, brandId=brand)
    
    db.session.add(Model)
    db.session.commit()

    return jsonify({'data': 'Success', 'id': id})


@app.route('/product', methods=['POST'])
def products():
    id = request.form['data']
    Products = tblProduct.query.with_entities(tblProduct.id, tblProduct.product, tblProduct.createdOn, tblProduct.price, tblProduct.photo, tblProduct.categoryId).filter_by(brandId=id).all()
    products = []
    for Product in Products:
        price = simplejson.dumps({"price": Product.price})
        price = json.loads(price)
        Category = tblCategory.query.get(Product.categoryId)
        arrival = datetime.now().date() - Product.createdOn.date()
        product = {
            'id': Product.id,
            'product': Product.product,
            'photo': Product.photo,
            'category': Category.category,
            'arrival': arrival.days
        }
        product.update(price)
        products.append(product)
    return jsonify(products)

@app.route('/product/photo/<id>', methods=['POST'])
def product_photo(id):
    alt = request.form['name']
    Product = tblProduct.query.get(id)
    if Product.photo != 'default.png':
        delete_photo('uploads', Product.photo)
    jsons = []
    for file in request.files:
        photo = request.files[file]
        extension = photo.filename.split('.')[1]
        filename = str(uuid4()) + '.' + extension
        photo.filename = filename
        uploaded = upload.save(photo)
        Product.photo = filename
        db.session.commit()
        json = {
            'photoId': Product.id,
            'src': filename,
            'alt': alt
        }
        jsons.append(json)
    return jsonify(jsons)

@app.route('/product/color/<id>', methods=['POST'])
def upload_color(id):
    hex = request.form['hex']
    color = request.form['color']
    cid = str(uuid4())
    Color = tblColor(id=cid, color=color, hex=hex, createdBy=current_user.id, productId=id)
    db.session.add(Color)
    db.session.commit()

    return jsonify({'id': cid, 'hex': hex, 'color': color})

@app.route('/color/photo/<id>', methods=['POST'])
def color_photo(id):
    cid = request.form['color']
    alt = request.form['name']
    jsons = []
    for file in request.files:
        photo = request.files[file]
        extension = photo.filename.split('.')[1]
        filename = str(uuid4()) + '.' + extension
        photo.filename = filename
        uploaded = upload.save(photo)
        pid = str(uuid4())
        Photo = tblPhoto(id=pid, src=filename, alt=alt, createdBy=current_user.id, colorId=cid, productId=id)
        db.session.add(Photo)
        db.session.commit()
    color = tblColor.query.get(cid)
    json = ColorSchema()
    result = json.dump(color)
    return jsonify(result)

@app.route('/product/<id>', methods=['POST', 'GET'])
def product(id):
    product = tblProduct.query.get(id)
    if request.method == 'POST':
        json = ProductSchema()
        result = json.dump(product)
        category = tblCategory.query.get(product.categoryId)
        c = CategorySchema()
        result['category'] = c.dump(category)
        return jsonify(result)
    return render_template('views/product_details.html', product=product)

@app.route('/value/add', methods=['POST'])
def add_value():
    product_id = request.form['product']
    property_id = request.form['property']
    value = request.form['value']
    price = request.form['price']
    currency = request.form['currency']
    description = request.form['description']

    id = str(uuid4())

    model = tblValue(id=id, value=value, price=price, currency=currency, description=description, createdBy=current_user.id, productId=product_id, propertyId=property_id)
    db.session.add(model)
    db.session.commit()
    return jsonify({'id': id, 'value': value, 'price': price, 'currency': currency, 'description': description, 'property': property_id})

@app.route('/product/save/<id>', methods=['POST'])
def save_product(id):
    Product = tblProduct.query.get(id)

    category = request.form['category']
    product = request.form['product']
    currency = request.form['currency']
    price = request.form['price']
    cost = request.form['cost']
    quantity = request.form['quantity']
    description = request.form['description']

    Product.product = product
    Product.currency = currency
    Product.price = price
    Product.description = description
    Product.categoryId = category
    Product.cost = cost
    Product.quantity = quantity

    db.session.commit()
    return jsonify({'data': 'success'})

@app.route('/product/remove/<id>', methods=['POST'])
def remove_product(id):
    product = tblProduct.query.get(id)
    if product.colors:
        for color in product.colors:
            if color.photos:
                for photo in color.photos:
                    delete_photo('uploads', photo.src)
    if product.photo != 'default.png':
        delete_photo('uploads', product.photo)
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'result': 'Success'})
    except:
        return jsonify({'result': 'Faild'})

@app.route('/value/save/<id>', methods=['POST'])
def save_value(id):
    value = tblValue.query.get(id)
    value.value = request.form['value']
    value.price = request.form['price']
    value.currency = request.form['currency']
    value.description = request.form['description']
    try:
        db.session.commit()
        return jsonify({'resutl': 'success', 'value': value.value, 'price': value.price, 'currency': value.currency, 'description': value.description})
    except:
        return jsonify({'resutl': 'failed'})

@app.route('/value/remove/<id>', methods=['POST'])
def remove_value(id):
    value = tblValue.query.get(id)
    db.session.delete(value)
    db.session.commit()
    return jsonify({'result': 'Success'})

@app.route('/color/<id>', methods=['POST'])
def get_color(id):
    color = tblColor.query.get(id)
    json = ColorSchema()
    result = json.dump(color)
    return jsonify(result)

@app.route('/color/save/<id>', methods=['POST'])
def save_color(id):
    color = tblColor.query.get(id)
    color.color = request.form['color']
    color.hex = request.form['hex']
    db.session.commit()
    return jsonify({'color': color.color, 'hex': color.hex})

@app.route('/color/remove/<id>', methods=['POST'])
def remove_color(id):
    color = tblColor.query.get(id)
    if color.photos:
        for photo in color.photos:
            delete_photo('uploads', photo.src)
    try:
        db.session.delete(color)
        db.session.commit()
        return jsonify({'result': 'Success', 'photos': []})
    except:
        return jsonify({'result': 'Failed'})

@app.route('/property/<id>', methods=['POST'])
def _property(id):
    category = tblCategory.query.get(id)
    c = CategorySchema()
    result_property = c.dump(category)
    
    product = tblProduct.query.get(request.form['product'])
    p = ProductSchema()
    if product:
        result_product = p.dump(product)
    else:
        result_product = ''
    

    return jsonify({'property': result_property, 'product': result_product})
