# models.py
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from werkzeug.utils import secure_filename
# دالة لإنشاء اتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db', timeout=60)  # الانتظار لمدة 60 ثانية عند الاتصال
    conn.row_factory = sqlite3.Row  # تعيين الصفوف كـ Row لتسهيل الوصول إلى الأعمدة
    return conn


def create_user(username, email, password):
    hashed_password = generate_password_hash(password)  # تشفير كلمة المرور
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                 (username, email, hashed_password))
    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال

def get_user_by_username(username):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()  # استرجاع بيانات المستخدم
    conn.close()  # إغلاق الاتصال
    return user

def create_deposit(depositor_name, account_number, phone_number, amount, deposit_date, deposit_time):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    conn.execute('INSERT INTO deposits (depositor_name, account_number, phone_number, amount, status, deposit_date, deposit_time) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                 (depositor_name, account_number, phone_number, amount, 'pending', deposit_date, deposit_time))
    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال
    
def get_all_deposits():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    deposits = conn.execute('SELECT * FROM deposits').fetchall()  # استرجاع جميع الإيداعات
    conn.close()  # إغلاق الاتصال
    return deposits

def get_all_products():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    products = conn.execute('SELECT * FROM products').fetchall()  # استرجاع جميع المنتجات
    conn.close()  # إغلاق الاتصال
    return products

def get_home_tools():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    home_tools = conn.execute('SELECT * FROM home_tools').fetchall()  # استرجاع جميع أدوات المنزل
    conn.close()  # إغلاق الاتصال
    return home_tools


def get_home_tools():
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    home_tools = conn.execute('SELECT * FROM home_tools').fetchall()  # استرجاع جميع أدوات المنزل
    conn.close()  # إغلاق الاتصال
    return home_tools

def search_products(query):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    results = conn.execute('SELECT * FROM products WHERE name LIKE ?', ('%' + query + '%',)).fetchall()  # استرجاع المنتجات التي تطابق استعلام البحث
    conn.close()  # إغلاق الاتصال
    return results

def get_product_by_id(product_id):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()  # استرجاع المنتج بناءً على معرفه
    conn.close()  # إغلاق الاتصال
    return product
def get_product_by_id(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        return {
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            # أضف أي خصائص أخرى تحتاجها
        }
    return None
def update_product(product_id, name, price, description, quantity, image_url, category):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    if category == 'phon':
        conn.execute(''' 
            UPDATE products 
            SET name = ?, price = ?, description = ?, quantity = ?, image_url = ? 
            WHERE id = ? 
        ''', (name, price, description, quantity, image_url, product_id))
    elif category == 'home_tools':
        conn.execute(''' 
            UPDATE home_tools 
            SET name = ?, price = ?, description = ?, quantity = ?, image_url = ? 
            WHERE id = ? 
        ''', (name, price, description, quantity, image_url, product_id))
    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال

def delete_product(product_id, product_type):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    if product_type == 'home_tools':
        conn.execute('DELETE FROM home_tools WHERE id = ?', (product_id,))  # حذف المنتج من جدول أدوات المنزل
    elif product_type == 'products':
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))  # حذف المنتج من جدول المنتجات
    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال

def add_product(name, price, description, quantity, image_url, category):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    if category == 'phon':
        conn.execute('INSERT INTO products (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)', 
                     (name, price, description, quantity, image_url))  # إدخال المنتج في جدول المنتجات
    elif category == 'home_tools':
        conn.execute('INSERT INTO home_tools (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)', 
                     (name, price, description, quantity, image_url))  # إدخال المنتج في جدول أدوات المنزل
    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال
def get_product_by_id(product_id):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()  # استرجاع المنتج بناءً على معرفه
    conn.close()  # إغلاق الاتصال
    return product
def get_orders_by_user(user_id):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    orders = conn.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,)).fetchall()  # استرجاع الطلبات الخاصة بالمستخدم
    conn.close()  # إغلاق الاتصال
    return orders

def insert_order(user_id, total):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    cursor = conn.cursor()  # إنشاء كائن المؤشر
    cursor.execute("INSERT INTO orders (user_id, order_date, total) VALUES (?, datetime('now'), ?)", 
                   (user_id, total))  # إدخال الطلب في جدول الطلبات
    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال

def vote_on_comment(user_id, comment_id, vote_type):
    conn = get_db_connection()  # إنشاء اتصال بقاعدة البيانات
    
    # تحقق مما إذا كان المستخدم قد صوت بالفعل
    existing_vote = conn.execute('SELECT * FROM votes WHERE user_id = ? AND comment_id = ?', (user_id, comment_id)).fetchone()
    if existing_vote:
        return False  # إذا كان المستخدم قد صوت بالفعل

    # إذا لم يصوت المستخدم، قم بتخزين التصويت
    conn.execute('INSERT INTO votes (user_id, comment_id, vote_type) VALUES (?, ?, ?)', (user_id, comment_id, vote_type))

    # تحديث عدد التصويتات في جدول التعليقات
    if vote_type == 'upvote':
        conn.execute('UPDATE comments SET upvotes = upvotes + 1 WHERE id = ?', (comment_id,))
    elif vote_type == 'downvote':
        conn.execute('UPDATE comments SET downvotes = downvotes + 1 WHERE id = ?', (comment_id,))

    conn.commit()  # حفظ التغييرات
    conn.close()  # إغلاق الاتصال
    return True  # إرجاع نجاح التصويت





# دالة لاسترجاع منتج بواسطة معرفه
def get_product_by_id(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        return {
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            # أضف أي خصائص أخرى تحتاجها
        }
    return None



def get_product_by_id(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        return {
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
        }
    return None

# دالة لإدارة السلة
def manage_cart(cart, product, action):
    if action == 'add':
        for item in cart:
            if item['id'] == product['id']:
                item['quantity'] += 1
                return cart
        cart.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': 1
        })
    elif action == 'remove':
        cart = [item for item in cart if item['id'] != product['id']]
    return cart

