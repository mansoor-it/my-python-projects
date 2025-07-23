# استيراد المكتبات اللازمة
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# إنشاء تطبيق Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # يجب أن تكون سرية لضمان أمان الجلسات

# تعيين مسار حفظ الصور
UPLOAD_FOLDER = 'static/images/'  # يمكنك تغيير هذا إلى المسار الذي تريده
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# التأكد من وجود المجلد
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # إنشاء المجلد إذا لم يكن موجودًا

# دالة لإنشاء اتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db', timeout=60)  # الانتظار لمدة 60 ثانية عند الاتصال
    conn.row_factory = sqlite3.Row  # تعيين الصفوف كـ Row لتسهيل الوصول إلى الأعمدة
    return conn

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')  # عرض الصفحة الرئيسية

# صفحة التسجيل
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # إذا كانت طريقة الطلب POST
        username = request.form['username']  # استلام اسم المستخدم
        email = request.form['email']  # استلام البريد الإلكتروني
        password = request.form['password']  # استلام كلمة المرور
        
        hashed_password = generate_password_hash(password)  # تشفير كلمة المرور

        conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
        # إدخال بيانات المستخدم في قاعدة البيانات
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
        conn.commit()  # حفظ التغييرات
        conn.close()  # إغلاق الاتصال
        return redirect(url_for('login'))  # إعادة التوجيه إلى صفحة تسجيل الدخول

    return render_template('register.html')  # عرض صفحة التسجيل

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == 'POST':  # إذا كانت طريقة الطلب POST
        username = request.form['username']  # استلام اسم المستخدم
        password = request.form['password']  # استلام كلمة المرور

        conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()  # استرجاع بيانات المستخدم
        conn.close()  # إغلاق الاتصال

        # تحقق من صحة كلمة المرور
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']  # تخزين معرف المستخدم في الجلسة
            session['username'] = user['username']  # تخزين اسم المستخدم في الجلسة

            if username.startswith("admin"):  # إذا كان اسم المستخدم يبدأ بـ "admin"
                return redirect(url_for('sting'))  # توجيه إلى صفحة المنتجات
            else:
                return redirect(url_for('products'))  # توجيه إلى الصفحة الرئيسية

        return render_template('login.html', error="بيانات الدخول غير صحيحة. يرجى المحاولة مرة أخرى.")  # عرض رسالة خطأ

    return render_template('login.html')  # عرض صفحة تسجيل الدخول

# صفحة الدفع
@app.route('/checkout', methods=['GET', 'POST'], strict_slashes=False)
def checkout():
    cart_items = session.get('cart', [])  # استرجاع عناصر السلة من الجلسة
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)  # حساب المبلغ الإجمالي

    if request.method == 'POST':  # إذا كانت طريقة الطلب POST
        flash('تمت معالجة الدفع بنجاح!')  # عرض رسالة نجاح
        session.pop('cart', None)  # إزالة السلة بعد الدفع
        return redirect(url_for('deposit'))  # إعادة التوجيه إلى صفحة الإيداع

    return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)  # عرض صفحة الدفع

# صفحة الإيداع
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':  # إذا كانت طريقة الطلب POST
        depositor_name = request.form['depositor_name']  # استلام اسم المودع
        account_number = request.form['account_number']  # استلام رقم الحساب
        phone_number = request.form['phone_number']  # استلام رقم الهاتف
        amount = request.form['amount']  # استلام المبلغ
        deposit_date = request.form['deposit_date']  # استلام تاريخ الإيداع
        deposit_time = request.form['deposit_time']  # استلام وقت الإيداع

        conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
        # إدخال بيانات الإيداع في قاعدة البيانات
        conn.execute('INSERT INTO deposits (depositor_name, account_number, phone_number, amount, status, deposit_date, deposit_time) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                     (depositor_name, account_number, phone_number, amount, 'pending', deposit_date, deposit_time))
        conn.commit()  # حفظ التغييرات
        conn.close()  # إغلاق الاتصال

        return redirect(url_for('ok'))  # إعادة التوجيه إلى صفحة النجاح
    
    return render_template('deposit.html')  # عرض صفحة الإيداع

# صفحة النجاح
@app.route('/ok')
def ok():
    return render_template('ok.html')  # عرض صفحة النجاح

# صفحة الواجهة
@app.route('/interfase')
def interfase():
    return render_template('interfase.html')  # عرض صفحة الواجهة

# دالة للتحقق من تسجيل الدخول
def is_logged_in():
    return 'user_id' in session  # تحقق مما إذا كان المستخدم مسجلاً الدخول

# صفحة المنتجات
@app.route('/sting')
def sting():
    if not is_logged_in():  # إذا لم يكن المستخدم مسجلاً الدخول
        flash("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")  # عرض رسالة خطأ
        return redirect(url_for('login'))  # توجيه المستخدم إلى صفحة تسجيل الدخول
    return render_template('sting.html')  # عرض صفحة المنتجات

# صفحة المدفوعات
@app.route('/payments')
def payments():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    deposits = conn.execute('SELECT * FROM deposits').fetchall()  # استرجاع جميع الإيداعات
    conn.close()  # إغلاق الاتصال
    return render_template('payments.html', deposits=deposits)  # عرض صفحة المدفوعات

# صفحة المنتجات
@app.route('/products', strict_slashes=True)
def products():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    if not is_logged_in():  # إذا لم يكن المستخدم مسجلاً الدخول
        flash("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")  # عرض رسالة خطأ
        return redirect(url_for('login'))  # توجيه المستخدم إلى صفحة تسجيل الدخول 
    products = conn.execute('SELECT * FROM products').fetchall()  # استرجاع جميع المنتجات
    conn.close()  # إغلاق الاتصال
    return render_template('products.html', products=products)  # عرض صفحة المنتجات

# صفحة نسخ المنتجات
@app.route('/products_copy')
def products_copy():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    products = conn.execute('SELECT * FROM products').fetchall()  # استرجاع جميع المنتجات
    conn.close()  # إغلاق الاتصال
    return render_template('products_copy.html', products=products)  # عرض صفحة نسخ المنتجات

# صفحة أدوات المنزل
@app.route('/home_tools')
def home_tools():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    home_tools = conn.execute('SELECT * FROM home_tools').fetchall()  # استرجاع جميع أدوات المنزل
    conn.close()  # إغلاق الاتصال
    return render_template('home_tools.html', home_tools=home_tools)  # عرض صفحة أدوات المنزل

# صفحة أدوات المنزل (تسجيل الدخول مطلوب)
@app.route('/st_home_tools')
def st_home_tools():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    if not is_logged_in():  # إذا لم يكن المستخدم مسجلاً الدخول
        flash("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")  # عرض رسالة خطأ
        return redirect(url_for('login'))  # توجيه المستخدم إلى صفحة تسجيل الدخول 
    home_tools = conn.execute('SELECT * FROM home_tools').fetchall()  # استرجاع جميع أدوات المنزل
    conn.close()  # إغلاق الاتصال
    return render_template('st_home_tools.html', home_tools=home_tools)  # عرض صفحة أدوات المنزل

# صفحة البحث
@app.route('/search')
def search():
    query = request.args.get('query', '')  # استلام استعلام البحث conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    
    results = conn.execute('SELECT * FROM products WHERE name LIKE ?', ('%' + query + '%',)).fetchall()  # استرجاع المنتجات التي تطابق استعلام البحث
    conn.close()  # إغلاق الاتصال
    return render_template('search_results.html', query=query, results=results)  # عرض نتائج البحث

# إضافة منتج إلى السلة
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()  # استرجاع المنتج بناءً على معرفه
    conn.close()  # إغلاق الاتصال

    if product:  # إذا كان المنتج موجودًا
        if 'cart' not in session:  # إذا لم تكن السلة موجودة في الجلسة
            session['cart'] = []  # إنشاء سلة جديدة

        for item in session['cart']:  # التحقق مما إذا كان المنتج موجودًا بالفعل في السلة
            if item['id'] == product['id']:
                item['quantity'] += 1  # زيادة الكمية
                session.modified = True  # تعديل الجلسة
                break
        else:
            session['cart'].append({  # إضافة المنتج إلى السلة
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': 1
            })
            session.modified = True  # تعديل الجلسة

    return redirect(url_for('cart'))  # إعادة التوجيه إلى صفحة السلة

# صفحة السلة
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])  # استرجاع عناصر السلة من الجلسة
    return render_template('cart.html', cart_items=cart_items)  # عرض صفحة السلة

# إزالة منتج من السلة
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart_items = session.get('cart', [])  # استرجاع عناصر السلة من الجلسة
    for item in cart_items:  # البحث عن المنتج في السلة
        if item['id'] == product_id:
            cart_items.remove(item)  # إزالة المنتج من السلة
            session.modified = True  # تعديل الجلسة
            break
    return redirect(url_for('cart'))  # إعادة التوجيه إلى صفحة السلة

# تعديل منتج
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    if not is_logged_in():  # إذا لم يكن المستخدم مسجلاً الدخول
        flash("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")  # عرض رسالة خطأ
        return redirect(url_for('login'))  # توجيه المستخدم إلى صفحة تسجيل الدخول 
    if request.method == 'POST':  # إذا كانت طريقة الطلب POST
        name = request.form['name']  # استلام اسم المنتج
        price = request.form['price']  # استلام سعر المنتج
        description = request.form['description']  # استلام وصف المنتج
        quantity = request.form['quantity']  # استلام كمية المنتج
        category = request.form['category']  # استلام القسم

        # معالجة تحميل الصورة
        if 'image' in request.files:  # إذا تم تحميل صورة
            file = request.files['image']
            if file.filename != '':  # إذا كان اسم الملف غير فارغ
                filename = secure_filename(file.filename)  # تأمين اسم الملف
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # حفظ الصورة
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # مسار الصورة
            else:
                image_path = None  # استخدم صورة سابقة أو تعيين قيمة افتراضية

        # تحديث المنتج في قاعدة البيانات بناءً على الفئة
        if category == 'phon':
            conn.execute(''' 
                UPDATE products 
                SET name = ?, price = ?, description = ?, quantity = ?, image_url = ? 
                WHERE id = ? 
            ''', (name, price, description, quantity, image_path, product_id))
        elif category == 'home_tools':
            conn.execute(''' 
                UPDATE home_tools 
                SET name = ?, price = ?, description = ?, quantity = ?, image_url = ? 
                WHERE id = ? 
            ''', (name, price, description, quantity, image_path, product_id))
        
        conn.commit()  # حفظ التغييرات
        conn.close()  # إغلاق الاتصال
        return redirect(url_for('products'))  # إعادة التوجيه إلى صفحة المنتجات
    else:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()  # استرجاع المنتج بناءً على معرفه
        if not product:  # إذا لم يتم العثور على المنتج
            product = conn.execute('SELECT * FROM home_tools WHERE id = ?', (product_id,)).fetchone()  # البحث في أدوات المنزل

        conn.close()  # إغلاق الاتصال
        return render_template('edit_product.html', product=product)  # عرض صفحة تعديل المنتج

# حذف منتج
@app.route('/delete_product/<int:product_id>/<product_type>', methods=['POST'])
def delete_product(product_id, product_type):
    if not is_logged_in():  # إذا لم يكن المستخدم مسجلاً الدخول
        flash("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")  # عرض رسالة خطأ
        return redirect(url_for('login'))  # توجيه المستخدم إلى صفحة تسجيل الدخول 
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    
    if product_type == 'home_tools':  # إذا كان نوع المنتج أدوات المنزل
        conn.execute('DELETE FROM home_tools WHERE id = ?', (product_id,))  # حذف المنتج من جدول أدوات المنزل
    elif product_type == 'products':  # إذا كان نوع المنتج منتجات
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))  # حذف المنتج من جدول المنتجات
    
    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال
    return redirect(url_for(product_type))  # إعادة التوجيه إلى صفحة المنتجات أو أدوات المنزل

# إضافة منتجات جديدة
@app.route('/add_products', methods=['GET', 'POST'])
def add_products():
    if not is_logged_in():  # إذا لم يكن المستخدم مسجلاً الدخول
        flash("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")  # عرض رسالة خطأ
        return redirect(url_for('login'))  # توجيه المستخدم إلى صفحة تسجيل الدخول 
    if request.method == 'POST':  # إذا كانت طريقة الطلب POST
        name = request.form['name']  # استلام اسم المنتج
        price = request.form['price']  # استلام سعر المنتج
        description = request.form['description']  # استلام وصف المنتج
        quantity = request.form['quantity']  # استلام كمية المنتج
        category = request.form['category']  # استلام القسم

        image_url = None  # متغير لتخزين مسار الصورة
        if 'image_url' in request.files:  # إذا تم تحميل صورة
            file = request.files['image_url']
            if file.filename != '':  # إذا كان اسم الملف غير فارغ
                filename = secure_filename(file.filename)  # تأمين اسم الملف
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # حفظ الصورة
                image_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # مسار الصورة

        conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
        
        # إضافة المنتج إلى الجدول المناسب بناءً على الفئة
        if category == 'phon':
            conn.execute('INSERT INTO products (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)', 
                         (name, price, description, quantity, image_url))  # إدخال المنتج في جدول المنتجات
        elif category == 'home_tools':
            conn.execute('INSERT INTO home_tools (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)', 
                         (name, price, description, quantity, image_url))  # إدخال المنتج في جدول أدوات المنزل

        conn.commit()  # حفظ التغييرات
        conn.close()  # إغلاق الاتصال
        
        return redirect(url_for('products', category=category))  # إعادة التوجيه إلى صفحة المنتجات

    return render_template('add_products.html')  # عرض صفحة إضافة المنتجات

# صفحة الطلبات
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    if request.method == 'POST':  # إذا كانت طريقة الطلب POST
        if 'user_id' in session:  # إذا كان المستخدم مسجلاً الدخول
            user_id = session['user_id']  # استلام معرف المستخدم
            product_id = request.form['product_id']  # استلام معرف المنتج
            quantity = int(request.form['quantity'])  # استلام الكمية

            cursor = conn.cursor()  # إنشاء كائن المؤشر
            cursor.execute("INSERT INTO orders (user_id, order_date, total) VALUES (?, datetime('now'), ?)", 
                           (user_id, quantity * 100))  # إدخال الطلب في جدول الطلبات
            conn.commit()  # حفظ التغييرات
        conn.close()  # إغلاق الاتصال

        return redirect(url_for('orders'))  # إعادة التوجيه إلى صفحة الطلبات

    orders = conn.execute('SELECT * FROM orders WHERE user_id = ?', (session.get('user_id', 1),)).fetchall()  # استرجاع الطلبات الخاصة بالمستخدم
    conn.close()  # إغلاق الاتصال
    return render_template('orders.html', orders=orders)  # عرض صفحة الطلبات

# التصويت على التعليقات
@app.route('/vote/<int:comment_id>', methods=['POST'])
def vote(comment_id):
    data = request.json  # استلام البيانات من الطلب
    user_id = data['user_id']  # استلام معرف المستخدم
    vote_type = data['vote_type']  # استلام نوع التصويت

    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    
    # تحقق مما إذا كان المستخدم قد صوت بالفعل
    existing_vote = conn.execute('SELECT * FROM votes WHERE user_id = ? AND comment_id = ?', (user_id, comment_id)).fetchone()
    if existing_vote:
        return {'success': False, 'message': 'لقد صوتت بالفعل على هذا التعليق.'}  # إذا كان المستخدم قد صوت بالفعل

    # إذا لم يصوت المستخدم، قم بتخزين التصويت
    conn.execute('INSERT INTO votes (user_id, comment_id, vote_type) VALUES (?, ?, ?)', (user_id, comment_id, vote_type))

    # تحديث عدد التصويتات في جدول التعليقات
    if vote_type == 'upvote':
        conn.execute('UPDATE comments SET upvotes = upvotes + 1 WHERE id = ?', (comment_id,))
    elif vote_type == 'downvote':
        conn.execute('UPDATE comments SET downvotes = downvotes + 1 WHERE id = ?', (comment_id,))

    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال
    return {'success': True}  # إرجاع نجاح التصويت

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True)  # تشغيل التطبيق في وضع التصحيح