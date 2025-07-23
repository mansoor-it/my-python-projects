# استيراد المكتبات اللازمة
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from flask_cors import CORS
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from logger_setup import setup_logger  # استدعاء ملف إعداد logger
from datetime import datetime, timezone, timedelta
import jwt
from functools import wraps
# استيراد الدوال من المودل
from models import (
    create_deposit,
    get_home_tools,
    search_products,
    get_product_by_id,
    update_product,
    delete_product,
    add_product,
    get_orders_by_user,
    insert_order,
    vote_on_comment,
    get_all_products,
    create_user,
    get_user_by_username,
    get_all_deposits,
    manage_cart
)
from session_logger import SessionLogger

# إنشاء تطبيق Flask
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_strong_secret_key_here'  # يجب أن تكون سرية لضمان أمان الجلسات
SECRET_KEY = app.secret_key 
 # نفس المفتاح لتوقيع JWT
# تعيين مسار حفظ الصور
UPLOAD_FOLDER = 'static/images/'  # يمكنك تغيير هذا إلى المسار الذي تريده
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# التأكد من وجود المجلد
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # إنشاء المجلد إذا لم يكن موجودًا

# إعداد logger
logger = setup_logger()

# إنشاء كائن لتسجيل الجلسات
session_logger = SessionLogger()

# ===================== Web Routes =====================

# دالة لإنشاء اتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db', timeout=60)
    conn.row_factory = sqlite3.Row
    return conn
    
# دالة لإنشاء توكن
def create_access_token(user_id, username, expires_delta=None):
    if expires_delta:
        
        expire = datetime.utcnow() + expires_delta     #datetime.utcnow(): يجلب الوقت الحالي بالتاريخ والساعة بصيغة UTC (التوقيت العالمي).

#+ expires_delta: نضيف مدة الصلاحية إلى الوقت الحالي.
    else:
        expire = datetime.utcnow() + timedelta(minutes=1)  # صلاحية 15 دقيقة افتراضياً
    #to_encode: متغير يمثل القاموس (dictionary) الذي يحتوي على البيانات التي سنضعها داخل التوكن.
    to_encode = {
        "exp": expire,#: اختصار لـ expiration (تاريخ انتهاء التوكن).
        "user_id": user_id,
        "username": username
    }
    #encoded_jwt: متغير يحتوي على التوكن النهائي بعد التشفير.
    encoded_jwt = jwt.encode(to_encode, "your-secret-key", algorithm="HS256")#تأخذ القاموس to_encode وتشفّره إلى توكن JWT.
    return encoded_jwt
#JWT اختصار لـ:
# JSON Web Token
# وهي طريقة آمنة لنقل معلومات (مثل هوية المستخدم) بين الطرف الخلفي (السيرفر) والطرف الأمامي (مثل تطبيق موبايل أو موقع) بشكل مشفر ومدقق.


# دالة لتحديث التوكن: تعني أنها مسؤولة عن إصدار توكن جديد بناءً على توكن قديم.
def refresh_access_token(token):#token: هو التوكن القديم الذي سيتم فحصه وتجديده (JWT string).
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return create_access_token(payload['user_id'], payload['username'])
    except jwt.ExpiredSignatureError:
#         إذا انتهت صلاحية التوكن (التاريخ في exp أصبح قديمًا)، يتم رفع هذا الخطأ.

# في هذه الحالة: التوكن منتهي ولا يمكن تحديثه.
        return None
#         إذا كان التوكن غير صحيح أو تم التلاعب به.

# مثال: تم تغييره يدويًا أو مفكوك بطريقة غير صحيحة.
    except jwt.InvalidTokenError:
        return None

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            # إنشاء توكن جديد
            access_token = create_access_token(user['id'], user['username'])
      #session تسمح بتخزين معلومات عن المستخدم طوال مدة تصفحه للموقع.      
            # حفظ التوكن في الجلسة
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['access_token'] = access_token
            
            logger.info(f'User logged in: {username}')
            return redirect(url_for('sting')) if username.startswith('admin') else redirect(url_for('products'))
        flash('بيانات الدخول غير صحيحة.')
    return render_template('login.html')

# صفحة لتحديث التوكن
@app.route('/refresh_token', methods=['POST'])
def refresh_token():
    if 'access_token' not in session:
        return jsonify({'error': 'No token found'}), 401
    
    new_token = refresh_access_token(session['access_token'])
    if new_token:
        session['access_token'] = new_token
        return jsonify({'access_token': new_token})
    return jsonify({'error': 'Invalid or expired token'}), 401

@app.route('/products', strict_slashes=True)
def products():
    if not is_logged_in():
        flash('يجب تسجيل الدخول')
        return redirect(url_for('login'))
    
    # تهيئة الوقت المتبقي بالقيمة الافتراضية (60 ثانية)
    time_remaining = 60
    
    # التحقق من وقت آخر نشاط للمستخدم
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])#fromisoformat(...): يحوّل التاريخ المخزن كنص إلى كائن datetime.

# time_diff: فرق الوقت بين الآن وآخر نشاط.

# total_seconds(): تُرجع الفارق بالثواني.

# max(0, ...): حتى لا تكون القيمة سالبة (إذا انتهى الوقت).
        time_diff = datetime.now() - last_activity
        time_remaining = max(0, 60 - time_diff.total_seconds())
        
        # إذا مرت أكثر من دقيقة
        if time_diff.total_seconds() > 60:
            # تسجيل معلومات الجلسة قبل مسحها
            session_logger.log_session(
#                 نحصل على اسم المستخدم من الجلسة.

# إذا لم يكن موجودًا، نستخدم 'unknown' كقيمة افتراضية.
                username=session.get('username', 'unknown'),
                session_start=session['last_activity'],#نحصل على توقيت بداية الجلسة (آخر مرة تم فيها التفاعل مع الموقع)
                session_duration=time_diff.total_seconds(),#يُفيد لمعرفة كم استغرقت الجلسة قبل أن تنتهي بسبب عدم النشاط.
                session_count=session.get('session_count', 0)#عدد المرات التي تفاعل فيها المستخدم مع الصفحة أثناء الجلسة.
            )
            session.clear()
            flash('انتهت مدة الجلسة، يرجى تسجيل الدخول مرة أخرى')
            return redirect(url_for('login'))
        
        # إذا كان هناك طلب تحديث للصفحة بعد ظهور التحذير
        if request.headers.get('X-Refresh-After-Warning') == 'true':
            # تسجيل معلومات الجلسة قبل تحديثها
            session_logger.log_session(
                username=session.get('username', 'unknown'),
                session_start=session['last_activity'],
                session_duration=time_diff.total_seconds(),
                session_count=session.get('session_count', 0)
            )
            # إعادة تعيين الجلسة
            session['last_activity'] = datetime.now().isoformat()
            session['session_count'] = session.get('session_count', 0) + 1
            time_remaining = 60
    
    # تحديث وقت آخر نشاط
    session['last_activity'] = datetime.now().isoformat()
    if 'session_count' not in session:
        session['session_count'] = 1
    
    products = get_all_products()
    return render_template('products.html', products=products, time_remaining=time_remaining)

# صفحة عرض السلة
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    return render_template('cart.html', cart_items=cart_items)

# إضافة منتج إلى السلة
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = get_product_by_id(product_id)
    if product:
        if 'cart' not in session:
            session['cart'] = []
        for item in session['cart']:
            if item['id'] == product['id']:
                item['quantity'] += 1
                session.modified = True
                break
        else:
            session['cart'].append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': 1
            })
            session.modified = True
    return redirect(url_for('cart'))

# إزالة منتج من السلة
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = manage_cart(session['cart'], {'id': product_id}, 'remove')
        session.modified = True
    return redirect(url_for('cart'))

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')

# صفحة التسجيل
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        create_user(username, email, password)
        logger.info(f'User registered: {username}')
        return redirect(url_for('login'))
    return render_template('register.html')

# # صفحة المنتجات

# @app.route('/products', strict_slashes=True)
# @token_required
# def products():
#     products = get_all_products()
#     return render_template('products.html', products=products)

# # صفحة تسجيل الدخول
# @app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = get_user_by_username(username)
#         if user and check_password_hash(user['password'], password):
#             session['user_id'] = user['id']
#             session['username'] = user['username']
#             logger.info(f'User logged in: {username}')
#             return redirect(url_for('sting')) if username.startswith('admin') else redirect(url_for('products'))
#         flash('بيانات الدخول غير صحيحة.')
#     return render_template('login.html')

# صفحة الدفع
@app.route('/checkout', methods=['GET', 'POST'], strict_slashes=False)
def checkout():
    cart_items = session.get('cart', [])
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
    if request.method == 'POST':
        flash('تمت معالجة الدفع بنجاح!')
        session.pop('cart', None)
        return redirect(url_for('deposit'))
    return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)

# صفحة الإيداع
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        depositor_name = request.form['depositor_name']
        account_number = request.form['account_number']
        phone_number = request.form['phone_number']
        amount = request.form['amount']
        deposit_date = request.form['deposit_date']
        deposit_time = request.form['deposit_time']
        create_deposit(depositor_name, account_number, phone_number, amount, deposit_date, deposit_time)
        logger.info(f'Deposit by {depositor_name} amount {amount}')
        return redirect(url_for('ok'))
    return render_template('deposit.html')

# صفحة النجاح
@app.route('/ok')
def ok():
    return render_template('ok.html')

# صفحة الواجهة
@app.route('/interfase')
def interfase():
    return render_template('interfase.html')

# دالة التحقق من تسجيل الدخول
def is_logged_in():
    return 'user_id' in session

# صفحة منتجات المدير (admin)
@app.route('/sting')
def sting():
    if not is_logged_in():
        flash('يجب تسجيل الدخول')
        return redirect(url_for('login'))
    return render_template('sting.html')

# صفحة المدفوعات
@app.route('/payments')
def payments():
    deposits = get_all_deposits()
    return render_template('payments.html', deposits=deposits)



# صفحة نسخ المنتجات
@app.route('/products_copy')
def products_copy():
    products = get_all_products()
    return render_template('products_copy.html', products=products)

# صفحة أدوات المنزل
@app.route('/home_tools')
def home_tools():
    home_tools = get_home_tools()
    return render_template('home_tools.html', home_tools=home_tools)

# صفحة أدوات المنزل للمستخدم
@app.route('/st_home_tools')
def st_home_tools():
    if not is_logged_in():
        flash('يجب تسجيل الدخول')
        return redirect(url_for('login'))
    home_tools = get_home_tools()
    return render_template('st_home_tools.html', home_tools=home_tools)

# صفحة البحث
@app.route('/search')
def search():
    query = request.args.get('query', '')
    results = search_products(query)
    return render_template('search_results.html', query=query, results=results)

# تعديل منتج
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not is_logged_in():
        flash('يجب تسجيل الدخول')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        quantity = request.form['quantity']
        category = request.form['category']
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        update_product(product_id, name, price, description, quantity, image_path, category)
        logger.info(f'Product updated: {name}')
        return redirect(url_for('products'))
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        product = conn.execute('SELECT * FROM home_tools WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    return render_template('edit_product.html', product=product)

# حذف منتج
@app.route('/delete_product/<int:product_id>/<product_type>', methods=['POST'])
def delete_product_route(product_id, product_type):
    if not is_logged_in():
        flash('يجب تسجيل الدخول')
        return redirect(url_for('login'))
    delete_product(product_id, product_type)
    logger.info(f'Product deleted: {product_id}')
    return redirect(url_for(product_type))

# إضافة منتج جديد
@app.route('/add_products', methods=['GET', 'POST'])
def add_products():
    if not is_logged_in():
        flash('يجب تسجيل الدخول')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        quantity = request.form['quantity']
        category = request.form['category']
        image_url = None
        if 'image_url' in request.files:
            file = request.files['image_url']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        add_product(name, price, description, quantity, image_url, category)
        logger.info(f'Product added: {name}')
        return redirect(url_for('products'))
    return render_template('add_products.html')

# صفحة الطلبات
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'POST' and 'user_id' in session:
        user_id = session['user_id']
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        insert_order(user_id, quantity * 100)
        return redirect(url_for('orders'))
    orders = get_orders_by_user(session.get('user_id', 1))
    return render_template('orders.html', orders=orders)

# التصويت على التعليقات
@app.route('/vote/<int:comment_id>', methods=['POST'])
def vote(comment_id):
    data = request.json
    user_id = data.get('user_id')
    vote_type = data.get('vote_type')
    success = vote_on_comment(user_id, comment_id, vote_type)
    return jsonify({'success': success})

# تشغيل التطبيق
if __name__ == '__main__':
    logger.info("Application started")
    try:
        logger.debug("Debugging information")
    except Exception as e:
        logger.error("An error occurred: %s", e)
    finally:
        logger.info("Application ended")
    app.run(debug=True)
