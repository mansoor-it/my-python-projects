from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from database import db
from flask import Flask, request, url_for
from werkzeug.utils import secure_filename
import time
import uuid
from bson.objectid import ObjectId

# استيراد محرك البحث بالصورة
from image_search.search_engine import ImageSearchEngine
from image_search.vectorizer import get_image_embedding, get_image_embedding_clip
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# -----------------------------------
# إعدادات المسارات للصور
# -----------------------------------

# المجلد الرئيسي للصور
MAIN_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# مجلد صور المنتجات
PRODUCTS_UPLOAD_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'products')

# مجلد صور المتاجر
STORES_UPLOAD_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'stores')

# مجلد صور الأقسام
CATEGORIES_UPLOAD_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'categories')

# المجلد الذي توجد به صور المنتجات (قاعدة البيانات) التي نريد البحث ضمنها
IMAGES_DB_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'jpg')

# مجلد حفظ الصورة التي سيقوم المستخدم برفعها لأجل البحث
SEARCH_UPLOAD_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'png')

# المجلد العام لرفع الصور (للمتاجر والمنتجات) - سيتم استخدامه للبحث فقط
UPLOAD_FOLDER = MAIN_UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PRODUCTS_UPLOAD_FOLDER'] = PRODUCTS_UPLOAD_FOLDER
app.config['STORES_UPLOAD_FOLDER'] = STORES_UPLOAD_FOLDER
app.config['CATEGORIES_UPLOAD_FOLDER'] = CATEGORIES_UPLOAD_FOLDER

# بناء محرك البحث FAISS عند بدء التطبيق
image_search_engine = ImageSearchEngine(IMAGES_DB_FOLDER)
image_search_engine.build_index()

# تهيئة قاعدة البيانات
print("\n=== تهيئة قاعدة البيانات ===")
try:
    # التأكد من الاتصال بقاعدة البيانات
    if not db.is_connected():
        print("❌ فشل الاتصال بقاعدة البيانات")
    else:
        print("✅ تم الاتصال بقاعدة البيانات بنجاح")
        
        # التحقق من وجود الأقسام الافتراضية
        categories = db.get_all_categories()
        if not categories:
            print("إنشاء الأقسام الافتراضية...")
            db._create_default_categories()
        else:
            print(f"تم العثور على {len(categories)} قسم")
            
        # التحقق من وجود متاجر
        stores = db.get_all_stores()
        if not stores:
            print("إنشاء متجر تجريبي...")
            db.create_sample_store()
        else:
            print(f"تم العثور على {len(stores)} متجر")
            
except Exception as e:
    print(f"❌ خطأ في تهيئة قاعدة البيانات: {str(e)}")
    import traceback
    print(traceback.format_exc())

# -----------------------------------
# إنشاء جميع مجلدات الصور إذا لم تكن موجودة
print("=== إنشاء مجلدات الصور ===")
print(f"المجلد الرئيسي: {MAIN_UPLOAD_FOLDER}")
print(f"مجلد صور المنتجات: {PRODUCTS_UPLOAD_FOLDER}")
print(f"مجلد صور المتاجر: {STORES_UPLOAD_FOLDER}")
print(f"مجلد صور الأقسام: {CATEGORIES_UPLOAD_FOLDER}")
print(f"مجلد صور قاعدة البيانات: {IMAGES_DB_FOLDER}")
print(f"مجلد صور البحث: {SEARCH_UPLOAD_FOLDER}")

try:
    os.makedirs(MAIN_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PRODUCTS_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(STORES_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(CATEGORIES_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(IMAGES_DB_FOLDER, exist_ok=True)
    os.makedirs(SEARCH_UPLOAD_FOLDER, exist_ok=True)
    print("✅ تم إنشاء جميع مجلدات الصور بنجاح")
except Exception as e:
    print(f"⚠️ تحذير: لم يتم إنشاء بعض المجلدات: {e}")
    print("سيتم إنشاؤها عند الحاجة")

def allowed_file(filename):
    """
    للتأكد من أن امتداد الملف ضمن المسموح به (png, jpg, jpeg).
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename, prefix="file"):
    """
    إنشاء اسم ملف فريد مع timestamp ومعرف عشوائي
    """
    # الحصول على امتداد الملف
    if '.' in original_filename:
        extension = original_filename.rsplit('.', 1)[1].lower()
    else:
        extension = 'jpg'
    
    # إنشاء معرف فريد
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    
    # إنشاء اسم الملف الجديد
    new_filename = f"{prefix}_{timestamp}_{unique_id}.{extension}"
    
    print(f"🔍 تم إنشاء اسم ملف فريد: {new_filename}")
    return new_filename

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
setattr(login_manager, 'login_view', 'login')

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.user_type = user_data['user_type']
        self.store_id = user_data.get('store_id')

@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

# تعريف الصور الافتراضية للأقسام
DEFAULT_CATEGORY_IMAGES = {
    'ملابس رجالية': 'https://images.unsplash.com/photo-1617137968427-85924c800a22?w=800&auto=format&fit=crop',
    'ملابس نسائية': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=800&auto=format&fit=crop',
    'أطفال': 'https://images.unsplash.com/photo-1622290291468-a28f7a7dc6a8?w=800&auto=format&fit=crop',
    'إلكترونيات': 'https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=800&auto=format&fit=crop',
    'هواتف': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&auto=format&fit=crop',
    'أحذية': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop'
}

print("\n=== قاموس الصور الافتراضية ===")
for name, image in DEFAULT_CATEGORY_IMAGES.items():
    print(f"اسم القسم في القاموس: '{name}'")
    print(f"طول الاسم: {len(name)}")
    print(f"الصورة: {image}")
    print("---")

# Routes
@app.route('/')
def home():
    try:
        # التحقق من الاتصال بقاعدة البيانات
        if not db.is_connected():
            flash('لا يمكن الاتصال بقاعدة البيانات حالياً', 'error')
            return render_template('home.html', categories=[], stores=[], products=[])

        # جلب الأقسام
        categories = db.get_all_categories()
        print("\n=== الأقسام الموجودة في قاعدة البيانات ===")
        for cat in categories:
            print(f"اسم القسم: '{cat['name']}'")
            print(f"طول الاسم: {len(cat['name'])}")
            print("---")
        
        # إضافة الصور الافتراضية للأقسام
        for category in categories:
            print(f"\nمعالجة القسم: '{category['name']}'")
            print(f"هل يوجد صورة في القاموس؟ {category['name'] in DEFAULT_CATEGORY_IMAGES}")
            print(f"مقارنة مباشرة:")
            for dict_name in DEFAULT_CATEGORY_IMAGES.keys():
                print(f"- '{dict_name}' == '{category['name']}'? {dict_name == category['name']}")
            category['image'] = DEFAULT_CATEGORY_IMAGES.get(category['name'], 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&auto=format&fit=crop')
            print(f"الصورة المخصصة: {category['image']}")

        # جلب المتاجر المميزة
        stores = db.get_featured_stores()
        
        # جلب المنتجات الأكثر مبيعاً
        products = db.get_top_products()
        
        return render_template('home.html', 
                             categories=categories,
                             stores=stores,
                             products=products)
    except Exception as e:
        print(f"خطأ في الصفحة الرئيسية: {str(e)}")
        flash('حدث خطأ أثناء تحميل الصفحة الرئيسية', 'error')
        return render_template('home.html', categories=[], stores=[], products=[])

@app.route('/category/<category>')
def category(category):
    if not db.is_connected():
        flash('لا يمكن الاتصال بقاعدة البيانات. يرجى المحاولة لاحقاً')
        return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
    
    try:
        category_data = db.get_category_by_id(category)
        if not category_data:
            flash('القسم غير موجود')
            return redirect(url_for('home'))
        
        stores = db.get_stores_by_category(category)
        print(f"تم جلب {len(stores)} متجر للقسم {category_data['name']}")  # للتأكد من عدد المتاجر
        
        return render_template('category.html', 
                             stores=stores, 
                             category=category_data)
    except Exception as e:
        print(f"خطأ في صفحة القسم: {str(e)}")  # للتأكد من الأخطاء
        flash('حدث خطأ أثناء جلب البيانات')
        return render_template('error.html', message=str(e))

@app.route('/store/<store_id>')
def store(store_id):
    if not db.is_connected():
        flash('لا يمكن الاتصال بقاعدة البيانات. يرجى المحاولة لاحقاً')
        return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
    
    try:
        store = db.get_store_by_id(store_id)
        if not store:
            flash('المتجر غير موجود')
            return redirect(url_for('home'))
        
        products = db.get_store_products(store_id)
        category = db.get_category_by_id(store['category'])
        
        return render_template('store/store.html',
                             store=store,
                             products=products,
                             category=category)
    except Exception as e:
        print(f"خطأ في صفحة المتجر: {str(e)}")  # للتأكد من الأخطاء
        flash('حدث خطأ أثناء جلب البيانات')
        return render_template('error.html', message=str(e))

@app.route('/store/<store_id>')
def store_view(store_id):
    """صفحة عرض المتجر للزبائن"""
    if not db.is_connected():
        flash('لا يمكن الاتصال بقاعدة البيانات. يرجى المحاولة لاحقاً')
        return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
    
    try:
        store = db.get_store_by_id(store_id)
        if not store:
            flash('المتجر غير موجود')
            return redirect(url_for('home'))
        
        products = db.get_store_products(store_id)
        category = db.get_category_by_id(store['category'])
        
        return render_template('store/store_view.html',
                             store=store,
                             products=products,
                             category=category)
    except Exception as e:
        print(f"خطأ في صفحة عرض المتجر: {str(e)}")
        flash('حدث خطأ أثناء جلب البيانات')
        return render_template('error.html', message=str(e))

@app.route('/store/dashboard')
@login_required
def store_dashboard():
    """لوحة تحكم صاحب المتجر"""
    print(f"\n=== محاولة الوصول إلى لوحة تحكم المتجر ===")
    print(f"المستخدم الحالي: {current_user.id}")
    print(f"نوع المستخدم: {current_user.user_type}")
    
    # التحقق من نوع المستخدم
    if current_user.user_type != 'store_owner':
        print("خطأ: المستخدم ليس صاحب متجر")
        flash('غير مصرح لك بالوصول إلى لوحة تحكم المتجر', 'danger')
        return redirect(url_for('home'))
    
    try:
        # التحقق من وجود متجر للمستخدم
        store = db.get_store_by_owner(current_user.id)
        if not store:
            print("لم يتم العثور على متجر للمستخدم")
            flash('يجب إنشاء متجر أولاً', 'warning')
            return redirect(url_for('create_store'))
        
        print(f"تم العثور على المتجر: {store.get('name', 'بدون اسم')}")
        
        # الحصول على المنتجات
        products = db.get_store_products(store['_id'])
        print(f"عدد المنتجات: {len(products)}")
        
        # الحصول على القسم
        category = db.get_category_by_id(store['category']) if store.get('category') else None
        
        # حساب الإحصائيات
        total_products = len(products)
        active_products = len([p for p in products if p.get('is_active', True)])
        
        # الحصول على الطلبات الجديدة (آخر 24 ساعة)
        new_orders = db.get_store_orders(store['_id'], days=1)
        new_orders_count = len(new_orders)
        
        # حساب إجمالي المبيعات
        total_sales = sum(order.get('total', 0) for order in new_orders)
        
        print("جاري تحميل قالب لوحة التحكم...")
        return render_template('store/dashboard.html',
                             store=store,
                             products=products,
                             category=category,
                             total_products=total_products,
                             active_products=active_products,
                             new_orders_count=new_orders_count,
                             total_sales=total_sales)
    except Exception as e:
        print(f"خطأ في لوحة تحكم المتجر: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء تحميل لوحة التحكم', 'error')
        return redirect(url_for('home'))

# مسارات السلة
@app.route('/cart')
@login_required
def cart():
    print("\n=== عرض السلة ===")
    print(f"المستخدم الحالي: {current_user.id}")
    
    if not db.is_connected():
        print("خطأ: لا يوجد اتصال بقاعدة البيانات")
        flash('لا يمكن الاتصال بقاعدة البيانات. يرجى المحاولة لاحقاً', 'error')
        return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
    
    try:
        print("جاري جلب محتويات السلة...")
        cart_items = db.get_cart(current_user.id)
        print(f"تم جلب {len(cart_items)} عنصر من السلة")
        
        if not cart_items:
            print("السلة فارغة")
            return render_template('cart.html', cart_items=[], total=0)
        
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        print(f"المجموع الكلي: {total}")
        
        return render_template('cart.html', cart_items=cart_items, total=total)
    except Exception as e:
        print(f"خطأ في عرض السلة: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء عرض السلة', 'error')
        return render_template('error.html', message=str(e))

@app.route('/cart/add/<product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    try:
        success = db.add_to_cart(current_user.id, product_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/cart/update/<product_id>', methods=['POST'])
def update_cart_item(product_id):
    """تحديث كمية منتج في السلة"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'يجب تسجيل الدخول أولاً'})
    
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            return jsonify({'success': False, 'message': 'الكمية يجب أن تكون 1 على الأقل'})
        
        # الحصول على الحجم واللون من المنتج في السلة
        cart = db.get_cart(current_user.id)
        item = next((item for item in cart if item['id'] == product_id), None)
        
        if not item:
            return jsonify({'success': False, 'message': 'المنتج غير موجود في السلة'})
        
        # تحديث الكمية
        success = db.update_cart_item_quantity(
            current_user.id,
            product_id,
            item['quantity'] + quantity,
            item.get('size'),
            item.get('color')
        )
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث الكمية'})
            
    except Exception as e:
        print(f"خطأ في تحديث الكمية: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث الكمية'})

@app.route('/cart/remove/<product_id>', methods=['POST'])
def remove_cart_item(product_id):
    """حذف منتج من السلة"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'يجب تسجيل الدخول أولاً'})
    
    try:
        # الحصول على الحجم واللون من المنتج في السلة
        cart = db.get_cart(current_user.id)
        item = next((item for item in cart if item['id'] == product_id), None)
        
        if not item:
            return jsonify({'success': False, 'message': 'المنتج غير موجود في السلة'})
        
        # حذف المنتج
        success = db.remove_from_cart(
            current_user.id,
            product_id,
            item.get('size'),
            item.get('color')
        )
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف المنتج'})
            
    except Exception as e:
        print(f"خطأ في حذف المنتج: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف المنتج'})

@app.route('/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    try:
        success = db.clear_cart(current_user.id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        name = request.form['name']
        
        if db.get_user_by_email(email):
            flash('البريد الإلكتروني مستخدم بالفعل')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        user_id = db.create_user(email, hashed_password, user_type, name)
        
        if user_id:
            flash('تم إنشاء الحساب بنجاح')
            return redirect(url_for('login'))
        else:
            flash('حدث خطأ أثناء إنشاء الحساب')
            return redirect(url_for('register'))
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Add None checks
        if not email or not password:
            flash('يرجى إدخال البريد الإلكتروني وكلمة المرور', 'danger')
            return render_template('auth/login.html')
        
        user = db.get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            login_user(User(user))
            flash('تم تسجيل الدخول بنجاح!', 'success')
            
            # التحقق من وجود متجر للمستخدم
            store = db.get_store_by_owner(user['_id'])
            if not store:
                return redirect(url_for('create_store'))
            return redirect(url_for('home'))
            
        flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة تحكم صاحب المتجر"""
    if current_user.user_type != 'store_owner':
        flash('غير مصرح لك بالوصول إلى لوحة التحكم', 'danger')
        return redirect(url_for('home'))
    
    try:
        # التحقق من وجود متجر للمستخدم
        store = db.get_store_by_owner(current_user.id)
        if not store:
            flash('يجب إنشاء متجر أولاً', 'warning')
            return redirect(url_for('create_store'))
        
        # الحصول على المنتجات
        products = db.get_store_products(store['_id'])
        
        # الحصول على القسم
        category = db.get_category_by_id(store['category']) if store.get('category') else None
        
        # حساب الإحصائيات
        total_products = len(products)
        active_products = len([p for p in products if p.get('is_active', True)])
        
        # الحصول على الطلبات الجديدة (آخر 24 ساعة)
        new_orders = db.get_store_orders(store['_id'], days=1)
        new_orders_count = len(new_orders)
        
        # حساب إجمالي المبيعات
        total_sales = sum(order.get('total', 0) for order in new_orders)
        
        return render_template('store/dashboard.html',
                             store=store,
                             products=products,
                             category=category,
                             total_products=total_products,
                             active_products=active_products,
                             new_orders_count=new_orders_count,
                             total_sales=total_sales)
    except Exception as e:
        print(f"خطأ في لوحة التحكم: {str(e)}")
        flash('حدث خطأ أثناء تحميل لوحة التحكم', 'error')
        return redirect(url_for('home'))

@app.route('/create_store', methods=['GET', 'POST'])
@login_required
def create_store():
    # السماح فقط لصاحب المتجر
    if current_user.user_type != 'store_owner':
        flash('غير مصرح لك بإنشاء متجر. فقط أصحاب المتاجر يمكنهم ذلك.', 'danger')
        return redirect(url_for('home'))
    # التحقق من وجود متجر للمستخدم
    store = db.get_store_by_owner(current_user.id)
    if store:
        flash('لديك متجر بالفعل!', 'warning')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            address = request.form.get('address')
            category = request.form.get('category')
            image = request.files.get('image')
            
            if not all([name, description, address, category]):
                flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
                return redirect(url_for('create_store'))
            
            filename = None
            if image and image.filename:
                try:
                    original_filename = secure_filename(image.filename)
                    print(f"🔍 اسم الملف الآمن: {original_filename}")
                    
                    # إنشاء اسم ملف فريد للمتجر
                    filename = generate_unique_filename(original_filename, "store")
                    
                    os.makedirs(app.config['STORES_UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['STORES_UPLOAD_FOLDER'], filename)
                    image.save(file_path)
                    print(f"✅ تم حفظ صورة المتجر بنجاح: {filename}")
                except Exception as e:
                    print(f"❌ حدث خطأ أثناء حفظ صورة المتجر: {e}")
                    flash('حدث خطأ أثناء حفظ صورة المتجر.', 'warning')
                
            store_id = db.create_store(name, description, address, category, filename, current_user.id)
            if store_id:
                flash('تم إنشاء المتجر بنجاح!', 'success')
                return redirect(url_for('home'))
            else:
                flash('حدث خطأ أثناء إنشاء المتجر', 'danger')
        except Exception as e:
            print(f"حدث خطأ أثناء إنشاء المتجر: {str(e)}")  # رسالة تصحيح
            flash(f'حدث خطأ: {str(e)}', 'danger')
            
    # جلب الأقسام من قاعدة البيانات
    categories = db.get_all_categories()
    return render_template('store/create_store.html', categories=categories)

@app.route('/store/edit', methods=['GET', 'POST'])
@login_required
def edit_store():
    if current_user.user_type != 'store_owner':
        return redirect(url_for('dashboard'))
    
    store = db.get_store_by_owner(current_user.id)
    if not store:
        return redirect(url_for('create_store'))
    
    if request.method == 'POST':
        store_data = {
            'name': request.form['name'],
            'address': request.form['address'],
            'category': request.form['category']
        }
        
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                try:
                    original_filename = secure_filename(image.filename)
                    # توليد اسم فريد للصورة
                    filename = generate_unique_filename(original_filename, "store")
                    os.makedirs(app.config['STORES_UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['STORES_UPLOAD_FOLDER'], filename)
                    image.save(file_path)
                    store_data['image'] = filename
                    print(f"تم حفظ صورة المتجر: {filename}")
                except Exception as e:
                    print(f"❌ حدث خطأ أثناء حفظ الصورة: {e}")
                    flash('حدث خطأ أثناء حفظ صورة المتجر.', 'warning')
        
        if db.update_store(store['_id'], store_data):
            flash('تم تحديث معلومات المتجر بنجاح')
            return redirect(url_for('dashboard'))
        else:
            flash('حدث خطأ أثناء تحديث معلومات المتجر')
    
    categories = db.get_all_categories()
    return render_template('edit_store.html', store=store, categories=categories)

@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.user_type != 'store_owner':
        return redirect(url_for('dashboard'))
    
    store = db.get_store_by_owner(current_user.id)
    if not store:
        return redirect(url_for('create_store'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            price_str = request.form.get('price')
            
            if not all([name, description, price_str]):
                flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
                return redirect(url_for('add_product'))
            
            try:
                price = float(price_str)  # type: ignore
            except (ValueError, TypeError):
                flash('السعر يجب أن يكون رقماً صحيحاً', 'danger')
                return redirect(url_for('add_product'))
            
            # جمع الأحجام والألوان المحددة
            pants_sizes = request.form.getlist('pants_sizes')
            clothes_sizes = request.form.getlist('clothes_sizes')
            colors = request.form.getlist('colors')
            
            filename = None
            if 'image' in request.files:
                image = request.files['image']
                print(f"🔍 تم العثور على ملف صورة: {image.filename}")
                if image and image.filename:
                    try:
                        original_filename = secure_filename(image.filename)
                        print(f"🔍 اسم الملف الآمن: {original_filename}")
                        
                        # إنشاء اسم ملف فريد للمنتج
                        filename = generate_unique_filename(original_filename, "product")
                        
                        os.makedirs(app.config['PRODUCTS_UPLOAD_FOLDER'], exist_ok=True)
                        file_path = os.path.join(app.config['PRODUCTS_UPLOAD_FOLDER'], filename)
                        print(f"🔍 مسار الحفظ: {file_path}")
                        image.save(file_path)
                        print(f"✅ تم حفظ صورة المنتج بنجاح: {filename}")
                        print(f"🔍 حجم الملف المحفوظ: {os.path.getsize(file_path)} bytes")
                    except Exception as e:
                        print(f"❌ حدث خطأ أثناء حفظ صورة المنتج: {e}")
                        flash('حدث خطأ أثناء حفظ صورة المنتج.', 'warning')
                        filename = None
                else:
                    print("❌ لم يتم العثور على ملف صورة صالح")
            else:
                print("❌ لم يتم إرسال ملف صورة في الطلب")
            
            print(f"🔍 اسم الصورة الذي سيتم حفظه في قاعدة البيانات: {filename}")
            
            product_id = db.create_product(
                name=name,
                description=description,
                price=price,
                store_id=str(store['_id']),
                category=store['category'],
                image=filename,
                pants_sizes=pants_sizes,
                clothes_sizes=clothes_sizes,
                colors=colors
            )
            
            if product_id:
                print(f"✅ تم إنشاء المنتج بنجاح مع المعرف: {product_id}")
                # التحقق من أن المنتج تم حفظه مع الصورة
                saved_product = db.get_product_by_id(product_id)
                if saved_product:
                    print(f"🔍 المنتج المحفوظ في قاعدة البيانات:")
                    print(f"   - الاسم: {saved_product.get('name')}")
                    print(f"   - الصورة: {saved_product.get('image')}")
                flash('تم إضافة المنتج بنجاح', 'success')
                return redirect(url_for('dashboard'))
            else:
                print("❌ فشل في إنشاء المنتج")
                flash('حدث خطأ أثناء إضافة المنتج', 'danger')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return render_template('store/add_product.html')

@app.route('/product/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.user_type != 'store_owner':
        return redirect(url_for('dashboard'))
    
    store = db.get_store_by_owner(current_user.id)
    if not store:
        return redirect(url_for('create_store'))
    
    product = db.get_product_by_id(product_id)
    if not product or product['store_id'] != str(store['_id']):
        flash('المنتج غير موجود')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        product_data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'price': float(request.form['price'])
        }
        
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                try:
                    original_filename = secure_filename(image.filename)
                    print(f"🔍 اسم الملف الآمن: {original_filename}")
                    
                    # إنشاء اسم ملف فريد للمنتج
                    filename = generate_unique_filename(original_filename, "product")
                    
                    os.makedirs(app.config['PRODUCTS_UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['PRODUCTS_UPLOAD_FOLDER'], filename)
                    image.save(file_path)
                    product_data['image'] = filename
                    print(f"✅ تم حفظ صورة المنتج بنجاح: {filename}")
                except Exception as e:
                    print(f"❌ حدث خطأ أثناء حفظ صورة المنتج: {e}")
                    flash('حدث خطأ أثناء حفظ صورة المنتج.', 'warning')
        
        if db.update_product(product_id, product_data):
            flash('تم تحديث المنتج بنجاح')
            return redirect(url_for('dashboard'))
        else:
            flash('حدث خطأ أثناء تحديث المنتج')
    
    return render_template('edit_product.html', product=product)

@app.route('/product/delete/<product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.user_type != 'store_owner':
        return jsonify({'success': False, 'message': 'غير مصرح لك بحذف المنتجات'})
    
    store = db.get_store_by_owner(current_user.id)
    if not store:
        return jsonify({'success': False, 'message': 'المتجر غير موجود'})
    
    product = db.get_product_by_id(product_id)
    if not product or product['store_id'] != str(store['_id']):
        return jsonify({'success': False, 'message': 'المنتج غير موجود'})
    
    if db.delete_product(product_id):
        return jsonify({'success': True, 'message': 'تم حذف المنتج بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف المنتج'})

@app.route('/profile')
@login_required
def profile():
    user_data = db.get_user_by_id(current_user.id)
    store = db.get_store_by_owner(current_user.id)
    return render_template('auth/profile.html', user=user_data, store=store)

# مسارات المشرف
@app.route('/admin')
@login_required
def admin_dashboard():
    """لوحة تحكم المشرف"""
    print("\n=== محاولة الوصول إلى لوحة تحكم المشرف ===")
    print(f"نوع المستخدم الحالي: {current_user.user_type}")
    
    if current_user.user_type != 'admin':
        print("خطأ: المستخدم ليس مشرف")
        flash('غير مصرح لك بالوصول إلى لوحة تحكم المشرف', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        # التحقق من الاتصال بقاعدة البيانات
        if not db.is_connected():
            print("خطأ: لا يوجد اتصال بقاعدة البيانات")
            flash('لا يمكن الاتصال بقاعدة البيانات حالياً', 'error')
            return render_template('admin/dashboard.html',
                                 total_stores=0,
                                 total_products=0,
                                 total_users=0,
                                 total_orders=0,
                                 recent_stores=[],
                                 recent_products=[],
                                 recent_users=[])
        
        print("✅ تم الاتصال بقاعدة البيانات بنجاح")
        
        # إحصائيات عامة
        total_stores = db.get_total_stores()
        total_products = db.get_total_products()
        total_users = db.get_total_users()
        total_orders = db.get_total_orders()
        
        print(f"📊 الإحصائيات:")
        print(f"   - المتاجر: {total_stores}")
        print(f"   - المنتجات: {total_products}")
        print(f"   - المستخدمين: {total_users}")
        print(f"   - الطلبات: {total_orders}")
        
        # آخر المتاجر المضافة
        recent_stores = db.get_recent_stores(5)
        
        # آخر المنتجات المضافة
        recent_products = db.get_recent_products(5)
        
        # آخر المستخدمين المسجلين
        recent_users = db.get_recent_users(5)
        
        print("✅ تم جلب جميع البيانات بنجاح")
        
        return render_template('admin/dashboard.html',
                             total_stores=total_stores,
                             total_products=total_products,
                             total_users=total_users,
                             total_orders=total_orders,
                             recent_stores=recent_stores,
                             recent_products=recent_products,
                             recent_users=recent_users)
    except Exception as e:
        print(f"❌ خطأ في لوحة تحكم المشرف: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء جلب البيانات', 'danger')
        return render_template('admin/stores.html', stores=[])

@app.route('/admin/stores/<store_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_store(store_id):
    """تعديل متجر"""
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة')
        return redirect(url_for('home'))
    
    try:
        store = db.get_store_by_id(store_id)
        if not store:
            flash('المتجر غير موجود')
            return redirect(url_for('admin_stores'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            address = request.form.get('address')
            category = request.form.get('category')
            is_featured = 'is_featured' in request.form
            
            image = request.files.get('image')
            filename = store.get('image')
            if image and image.filename:
                try:
                    original_filename = secure_filename(image.filename)
                    import time, uuid
                    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
                    unique_id = str(uuid.uuid4())[:8]
                    timestamp = int(time.time())
                    filename = f"store_{timestamp}_{unique_id}.{extension}"
                    stores_folder = app.config['STORES_UPLOAD_FOLDER']
                    os.makedirs(stores_folder, exist_ok=True)
                    file_path = os.path.join(stores_folder, filename)
                    image.save(file_path)
                    print(f"تم حفظ صورة المتجر: {filename}")
                except Exception as e:
                    print(f"❌ حدث خطأ أثناء حفظ الصورة: {e}")
                    flash('حدث خطأ أثناء حفظ صورة المتجر.', 'warning')
            
            success = db.update_store(store_id, {
                'name': name,
                'description': description,
                'address': address,
                'category': category,
                'image': filename,
                'is_featured': is_featured
            })
            
            if success:
                flash('تم تحديث المتجر بنجاح')
                return redirect(url_for('admin_stores'))
            else:
                flash('حدث خطأ أثناء تحديث المتجر')
        
        categories = db.get_all_categories()
        return render_template('admin/edit_store.html', 
                             store=store, 
                             categories=categories)
    except Exception as e:
        flash('حدث خطأ أثناء تحديث المتجر')
        return render_template('error.html', message=str(e))

@app.route('/admin/stores/<store_id>/delete', methods=['POST'])
@login_required
def admin_delete_store(store_id):
    """حذف متجر"""
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        success = db.delete_store(store_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/products')
@login_required
def admin_products():
    """إدارة المنتجات"""
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        products = db.get_all_products()
        return render_template('admin/products.html', products=products)
    except Exception as e:
        flash('حدث خطأ أثناء جلب البيانات')
        return render_template('error.html', message=str(e))

@app.route('/admin/products/<product_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    """تعديل منتج"""
    
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة')
        return redirect(url_for('home'))
    
    try:
        product = db.get_product_by_id(product_id)
        if not product:
            flash('المنتج غير موجود')
            return redirect(url_for('admin_products'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            price_str = request.form.get('price')
            store_id = request.form.get('store_id')
            category = request.form.get('category')
            
            # Add None checks and validation
            if not all([name, description, price_str, store_id, category]):
                flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
                return redirect(url_for('admin_edit_product', product_id=product_id))
            
            try:
                if not price_str:
                    flash('السعر مطلوب', 'danger')
                    return redirect(url_for('admin_edit_product', product_id=product_id))
                price = float(price_str)
            except (ValueError, TypeError):
                flash('السعر يجب أن يكون رقماً صحيحاً', 'danger')
                return redirect(url_for('admin_edit_product', product_id=product_id))
            
            pants_sizes = request.form.getlist('pants_sizes')
            clothes_sizes = request.form.getlist('clothes_sizes')
            colors = request.form.getlist('colors')
            
            image = request.files.get('image')
            filename = product.get('image')
            if image and image.filename:
                try:
                    original_filename = secure_filename(image.filename)
                    import time, uuid
                    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
                    unique_id = str(uuid.uuid4())[:8]
                    timestamp = int(time.time())
                    filename = f"product_{timestamp}_{unique_id}.{extension}"
                    products_folder = app.config['PRODUCTS_UPLOAD_FOLDER']
                    os.makedirs(products_folder, exist_ok=True)
                    file_path = os.path.join(products_folder, filename)
                    image.save(file_path)
                    print(f"✅ تم حفظ صورة المنتج بنجاح: {filename}")
                except Exception as e:
                    print(f"❌ حدث خطأ أثناء حفظ الصورة: {e}")
                    flash('حدث خطأ أثناء حفظ صورة المنتج.', 'warning')
            
            success = db.update_product(product_id, {
                'name': name,
                'description': description,
                'price': price,
                'store_id': store_id,
                'category': category,
                'image': filename,
                'pants_sizes': pants_sizes,
                'clothes_sizes': clothes_sizes,
                'colors': colors
            })
            
            if success:
                flash('تم تحديث المنتج بنجاح')
                return redirect(url_for('admin_products'))
            else:
                flash('حدث خطأ أثناء تحديث المنتج')
        
        stores = db.get_all_stores()
        categories = db.get_all_categories()
        return render_template('admin/edit_product.html', 
                             product=product, 
                             stores=stores,
                             categories=categories)
    except Exception as e:
        flash('حدث خطأ أثناء تحديث المنتج')
        return render_template('error.html', message=str(e))

@app.route('/admin/products/<product_id>/delete', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    """حذف منتج"""
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        success = db.delete_product(product_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/users')
@login_required
def admin_users():
    """إدارة المستخدمين"""
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        users = db.get_all_users()
        # جلب معلومات المتاجر لكل مستخدم
        for user in users:
            if user['user_type'] == 'store_owner':
                store = db.get_store_by_owner(str(user['_id']))
                if store:
                    user['store_id'] = str(store['_id'])
                    user['store_name'] = store['name']
                else:
                    user['store_id'] = None
                    user['store_name'] = None
        return render_template('admin/users.html', users=users)
    except Exception as e:
        flash('حدث خطأ أثناء جلب البيانات')
        return render_template('error.html', message=str(e))

@app.route('/admin/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    """تعديل مستخدم"""
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة')
        return redirect(url_for('home'))
    
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            flash('المستخدم غير موجود')
            return redirect(url_for('admin_users'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            name = request.form.get('name')
            user_type = request.form.get('user_type')
            # دعم رفع صورة المستخدم
            image = request.files.get('image')
            filename = user.get('image')
            if image and image.filename:
                try:
                    from werkzeug.utils import secure_filename
                    import os
                    original_filename = secure_filename(image.filename)
                    # إنشاء اسم ملف فريد
                    import time, uuid
                    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
                    unique_id = str(uuid.uuid4())[:8]
                    timestamp = int(time.time())
                    filename = f"user_{timestamp}_{unique_id}.{extension}"
                    users_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'users')
                    os.makedirs(users_folder, exist_ok=True)
                    file_path = os.path.join(users_folder, filename)
                    image.save(file_path)
                except Exception as e:
                    print(f"❌ خطأ أثناء حفظ صورة المستخدم: {e}")
                    flash('حدث خطأ أثناء حفظ صورة المستخدم.', 'warning')
            
            success = db.update_user(user_id, {
                'email': email,
                'name': name,
                'user_type': user_type,
                'image': filename
            })
            
            if success:
                flash('تم تحديث المستخدم بنجاح')
                return redirect(url_for('admin_users'))
            else:
                flash('حدث خطأ أثناء تحديث المستخدم')
        
        return render_template('admin/edit_user.html', user=user)
    except Exception as e:
        flash('حدث خطأ أثناء تحديث المستخدم')
        return render_template('error.html', message=str(e))

@app.route('/admin/users/<user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """حذف مستخدم"""
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        success = db.delete_user(user_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """تسجيل دخول المشرف"""
    print("\n=== محاولة تسجيل دخول المشرف ===")
    
    # إذا كان المستخدم مسجل دخوله بالفعل كمشرف، قم بتوجيهه إلى لوحة التحكم
    if current_user.is_authenticated:
        print(f"المستخدم مسجل دخوله بالفعل. نوع المستخدم: {current_user.user_type}")
        if current_user.user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"محاولة تسجيل دخول: {email}")
        
        if db.check_admin_credentials(email, password):
            user = db.get_user_by_email(email)
            if user:
                print(f"تم العثور على المستخدم: {user.get('email')}")
                print(f"نوع المستخدم: {user.get('user_type')}")
                login_user(User(user))
                flash('تم تسجيل الدخول بنجاح!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                print("لم يتم العثور على المستخدم بعد التحقق من البيانات")
        else:
            print("فشل التحقق من بيانات تسجيل الدخول")
            
        flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/setup', methods=['GET', 'POST'])
def admin_setup():
    """إنشاء حساب المشرف الأول"""
    # التحقق من وجود مشرفين في النظام
    if db.get_admin_count() > 0:
        flash('تم إعداد المشرف بالفعل', 'warning')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if not all([email, password, name]):
            flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
            return redirect(url_for('admin_setup'))
        
        # التحقق من عدم وجود البريد الإلكتروني
        if db.get_user_by_email(email):
            flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
            return redirect(url_for('admin_setup'))
        
        # إنشاء حساب المشرف
        if not password:
            flash('كلمة المرور مطلوبة', 'danger')
            return redirect(url_for('admin_setup'))
        hashed_password = generate_password_hash(password)
        user_id = db.create_user(email, hashed_password, 'admin', name)
        
        if user_id:
            flash('تم إنشاء حساب المشرف بنجاح! يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('admin_login'))
        else:
            flash('حدث خطأ أثناء إنشاء حساب المشرف', 'danger')
    
    return render_template('admin/setup.html')

@app.route('/checkout')
@login_required
def checkout():
    print("\n=== بدء عملية إتمام الشراء ===")
    print(f"المستخدم الحالي: {current_user.id}")
    
    if not db.is_connected():
        print("خطأ: لا يوجد اتصال بقاعدة البيانات")
        flash('لا يمكن الاتصال بقاعدة البيانات. يرجى المحاولة لاحقاً', 'error')
        return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
    
    try:
        print("جاري جلب محتويات السلة...")
        cart_items = db.get_cart(current_user.id)
        print(f"تم جلب {len(cart_items)} عنصر من السلة")
        
        if not cart_items:
            print("السلة فارغة")
            flash('السلة فارغة', 'warning')
            return redirect(url_for('cart'))
        
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        print(f"المجموع الكلي: {total}")
        
        print("جاري تحميل صفحة إتمام الشراء...")
        return render_template('checkout.html', cart_items=cart_items, total=total)
    except Exception as e:
        print(f"خطأ في صفحة إتمام الشراء: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء تحميل صفحة إتمام الشراء', 'error')
        return redirect(url_for('cart'))

@app.route('/process_order', methods=['POST'])
@login_required
def process_order():
    print("\n=== بدء معالجة الطلب ===")
    print(f"المستخدم الحالي: {current_user.id}")
    
    if not db.is_connected():
        print("خطأ: لا يوجد اتصال بقاعدة البيانات")
        flash('لا يمكن الاتصال بقاعدة البيانات. يرجى المحاولة لاحقاً', 'error')
        return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
    
    try:
        print("جاري جلب محتويات السلة...")
        cart_items = db.get_cart(current_user.id)
        print(f"تم جلب {len(cart_items)} عنصر من السلة")
        
        if not cart_items:
            print("السلة فارغة")
            flash('السلة فارغة', 'warning')
            return redirect(url_for('cart'))
        
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        print(f"المجموع الكلي: {total}")
        
        # جلب بيانات النموذج
        payment_method = request.form.get('payment_method')
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        print(f"طريقة الدفع: {payment_method}")
        print(f"الاسم: {name}")
        print(f"الهاتف: {phone}")
        print(f"العنوان: {address}")
        
        # التحقق من البيانات المطلوبة
        if not all([payment_method, name, phone, address]):
            print("بيانات ناقصة في النموذج")
            flash('يرجى ملء جميع الحقول المطلوبة', 'warning')
            return redirect(url_for('checkout'))
        
        transfer_image = None
        if payment_method == 'bank':
            print("التحقق من صورة إشعار التحويل...")
            if 'transfer_image' not in request.files:
                print("لم يتم إرفاق صورة إشعار التحويل")
                flash('يرجى إرفاق صورة إشعار التحويل', 'warning')
                return redirect(url_for('checkout'))
            
            file = request.files['transfer_image']
            if file.filename == '':
                print("لم يتم اختيار ملف")
                flash('لم يتم اختيار ملف', 'warning')
                return redirect(url_for('checkout'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename) if file.filename else f"transfer_{int(time.time())}.jpg"
                # التأكد من وجود المجلد قبل حفظ الصورة
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                transfer_image = filename
                print(f"تم حفظ صورة إشعار التحويل: {filename}")
            else:
                print("نوع الملف غير مسموح به")
                flash('نوع الملف غير مسموح به', 'warning')
                return redirect(url_for('checkout'))
        
        # إنشاء الطلب
        print("جاري إنشاء الطلب...")
        order_id = db.create_order(
            current_user.id,
            cart_items,
            total,
            payment_method,
            name,
            phone,
            address,
            transfer_image
        )
        
        if order_id:
            print(f"تم إنشاء الطلب بنجاح: {order_id}")
            # تفريغ السلة
            db.clear_cart(current_user.id)
            flash('تم إنشاء الطلب بنجاح', 'success')
            return redirect(url_for('order_success', order_id=order_id))
        else:
            print("فشل في إنشاء الطلب")
            flash('حدث خطأ أثناء إنشاء الطلب', 'error')
            return redirect(url_for('checkout'))
            
    except Exception as e:
        print(f"خطأ في معالجة الطلب: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء معالجة الطلب', 'error')
        return redirect(url_for('checkout'))

@app.route('/order_success/<order_id>')
@login_required
def order_success(order_id):
    order = db.get_order_by_id(order_id)
    if not order or order['user_id'] != current_user.id:
        flash('الطلب غير موجود', 'error')
        return redirect(url_for('home'))
    
    # تحويل ObjectId إلى نص للاستخدام في القالب
    if order and '_id' in order:
        order['_id_str'] = str(order['_id'])
    
    # التأكد من أن items قائمة صحيحة
    if 'items' in order:
        if not isinstance(order['items'], list):
            order['items'] = []
        order['items_count'] = len(order['items'])
    else:
        order['items'] = []
        order['items_count'] = 0
    
    return render_template('order_success.html', order=order)

@app.route('/admin/orders')
@login_required
def admin_orders():
    """إدارة الطلبات"""
    print("\n=== عرض قائمة الطلبات للمشرف ===")
    
    if current_user.user_type != 'admin':
        print("خطأ: المستخدم غير مصرح له بالوصول")
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        # التأكد من الاتصال بقاعدة البيانات
        if not db.ensure_connection():
            print("خطأ: لا يمكن الاتصال بقاعدة البيانات")
            flash('لا يمكن الاتصال بقاعدة البيانات', 'error')
            return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
        
        # جلب معايير التصفية
        status = request.args.get('status')
        payment_method = request.args.get('payment_method')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        print(f"معايير التصفية:")
        print(f"- الحالة: {status}")
        print(f"- طريقة الدفع: {payment_method}")
        print(f"- من تاريخ: {start_date}")
        print(f"- إلى تاريخ: {end_date}")
        
        # جلب الطلبات مع التصفية
        print("جاري جلب الطلبات...")
        orders = db.get_all_orders(
            status=status,
            payment_method=payment_method,
            start_date=start_date,
            end_date=end_date
        )
        
        if not orders:
            print("لم يتم العثور على طلبات")
            flash('لا توجد طلبات حالياً', 'info')
        else:
            print(f"تم جلب {len(orders)} طلب")
        
        print("جاري تحميل قالب الطلبات...")
        return render_template('admin/orders.html', orders=orders)
        
    except Exception as e:
        print(f"خطأ في جلب الطلبات: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء جلب الطلبات', 'error')
        return render_template('error.html', message=str(e))

@app.route('/admin/orders/<order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('home'))
    
    try:
        # تحديث حالة الطلب إلى مكتمل
        if db.update_order_status(order_id, 'completed'):
            # حذف الطلب بعد إكماله
            flash('تم إكمال الطلب بنجاح', 'success')
        else:
            flash('حدث خطأ أثناء إكمال الطلب', 'danger')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/orders/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('home'))
    
    if db.update_order_status(order_id, 'cancelled'):
        flash('تم إلغاء الطلب بنجاح', 'success')
    else:
        flash('حدث خطأ أثناء إلغاء الطلب', 'danger')
    
    return redirect(url_for('admin_orders'))

@app.route('/product/<product_id>')
def product_details(product_id):
    """صفحة تفاصيل المنتج"""
    if not db.is_connected():
        flash('لا يمكن الاتصال بقاعدة البيانات. يرجى المحاولة لاحقاً')
        return render_template('error.html', message='خطأ في الاتصال بقاعدة البيانات')
    
    try:
        product = db.get_product_by_id(product_id)
        if not product:
            flash('المنتج غير موجود')
            return redirect(url_for('home'))
        
        store = db.get_store_by_id(product['store_id'])
        if not store:
            flash('المتجر غير موجود')
            return redirect(url_for('home'))
        
        return render_template('store/product_details.html',
                             product=product,
                             store=store)
    except Exception as e:
        print(f"خطأ في صفحة تفاصيل المنتج: {str(e)}")
        flash('حدث خطأ أثناء جلب البيانات')
        return render_template('error.html', message=str(e))

def get_image_url(image_filename, content_type="product"):
    """
    الحصول على مسار الصورة الصحيح بناءً على نوع المحتوى
    """
    if not image_filename:
        return None
    
    # إذا كانت الصورة رابط خارجي، نعيده كما هو
    if image_filename.startswith('http'):
        return image_filename
    
    # إذا كانت الصورة من Unsplash، نعيدها كما هي
    if 'unsplash.com' in image_filename:
        return image_filename
    
    # مسارات الصور المحلية
    if content_type == "store":
        return url_for('static', filename=f'uploads/stores/{image_filename}')
    elif content_type == "product":
        return url_for('static', filename=f'uploads/products/{image_filename}')
    elif content_type == "category":
        return url_for('static', filename=f'uploads/categories/{image_filename}')
    elif content_type == "user":
        return url_for('static', filename=f'uploads/users/{image_filename}')
    else:
        return url_for('static', filename=f'uploads/{image_filename}')

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.context_processor
def inject_image_helpers():
    """إضافة دوال مساعدة للصور في جميع القوالب"""
    return {
        'get_image_url': get_image_url
    }

@app.route('/admin/stores/<store_id>/toggle-featured', methods=['POST'])
@login_required
def toggle_featured_store(store_id):
    """تحديد/إلغاء تحديد المتجر كمميز"""
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        is_featured = request.json.get('is_featured', False) if request.json else False
        
        # تحديث حالة التميز في قاعدة البيانات
        success = db.update_store(store_id, {'is_featured': is_featured})
        
        if success:
            status_text = "مميز" if is_featured else "غير مميز"
            return jsonify({
                'success': True, 
                'message': f'تم تحديث حالة المتجر إلى {status_text}'
            })
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث حالة التميز'})
            
    except Exception as e:
        print(f"خطأ في تحديث حالة التميز: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/stores/<store_id>/toggle-status', methods=['POST'])
@login_required
def toggle_store_status(store_id):
    """تفعيل/إلغاء تفعيل المتجر"""
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        is_active = request.json.get('is_active', False) if request.json else False
        
        # تحديث حالة المتجر في قاعدة البيانات
        success = db.update_store(store_id, {'is_active': is_active})
        
        if success:
            status_text = "مفعل" if is_active else "غير مفعل"
            return jsonify({
                'success': True, 
                'message': f'تم تحديث حالة المتجر إلى {status_text}'
            })
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث حالة المتجر'})
            
    except Exception as e:
        print(f"خطأ في تحديث حالة المتجر: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/products/<product_id>/toggle-featured', methods=['POST'])
@login_required
def toggle_featured_product(product_id):
    """تحديد/إلغاء تحديد المنتج كمميز"""
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        is_featured = request.json.get('is_featured', False) if request.json else False
        # success = db.toggle_featured_product(product_id, is_featured)  # Method not implemented
        success = False  # Placeholder
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/store/<store_id>/rate', methods=['POST'])
@login_required
def rate_store(store_id):
    """تقييم المتجر"""
    try:
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '')
        
        if not 1 <= rating <= 5:
            return jsonify({'success': False, 'message': 'التقييم يجب أن يكون بين 1 و 5'})
        
        # التحقق من وجود تقييم سابق
        # if db.has_user_rated_store(store_id, current_user.id):  # Method not implemented
        #     # تحديث التقييم
        #     success = db.update_store_rating(store_id, current_user.id, rating, comment)  # Method not implemented
        # else:
        #     # إضافة تقييم جديد
        #     success = db.add_store_rating(store_id, current_user.id, rating, comment)  # Method not implemented
        
        success = False  # Placeholder
        if success:
            return jsonify({'success': True, 'message': 'تم إضافة التقييم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ أثناء إضافة التقييم'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/product/<product_id>/rate', methods=['POST'])
@login_required
def rate_product(product_id):
    """تقييم المنتج"""
    try:
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '')
        
        if not 1 <= rating <= 5:
            return jsonify({'success': False, 'message': 'التقييم يجب أن يكون بين 1 و 5'})
        
        # التحقق من وجود تقييم سابق
        # if db.has_user_rated_product(product_id, current_user.id):  # Method not implemented
        #     # تحديث التقييم
        #     success = db.update_product_rating(product_id, current_user.id, rating, comment)  # Method not implemented
        # else:
        #     # إضافة تقييم جديد
        #     success = db.add_product_rating(product_id, current_user.id, rating, comment)  # Method not implemented
        
        success = False  # Placeholder
        if success:
            return jsonify({'success': True, 'message': 'تم إضافة التقييم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ أثناء إضافة التقييم'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/store/<store_id>/ratings')
def get_store_ratings(store_id):
    """جلب تقييمات المتجر"""
    try:
        # ratings = db.get_store_ratings(store_id)  # Method not implemented
        # average_rating = db.get_store_average_rating(store_id)  # Method not implemented
        ratings = []  # Placeholder
        average_rating = 0  # Placeholder
        return jsonify({
            'success': True,
            'ratings': ratings,
            'average_rating': average_rating
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/product/<product_id>/ratings')
def get_product_ratings(product_id):
    """جلب تقييمات المنتج"""
    try:
        # ratings = db.get_product_ratings(product_id)  # Method not implemented
        # average_rating = db.get_product_average_rating(product_id)  # Method not implemented
        ratings = []  # Placeholder
        average_rating = 0  # Placeholder
        return jsonify({
            'success': True,
            'ratings': ratings,
            'average_rating': average_rating
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@app.route('/search-by-image', methods=['POST'])
def search_by_image():
    """البحث بالصورة - مقارنة مباشرة مع منتجات قاعدة البيانات"""
    print("\n=== بدء البحث بالصورة ===")
    
    if 'image' not in request.files:
        print("❌ لم يتم اختيار صورة")
        flash('لم يتم اختيار صورة', 'warning')
        return redirect(url_for('home'))

    file = request.files['image']
    if file.filename == '':
        print("❌ اسم الملف فارغ")
        flash('لم يتم اختيار صورة', 'warning')
        return redirect(url_for('home'))

    if file and allowed_file(file.filename):
        try:
            print(f"✅ تم استلام صورة: {file.filename}")
            
            # حفظ الصورة مؤقتاً
            filename = secure_filename(file.filename) if file.filename else f"search_image_{int(time.time())}.jpg"
            if len(filename) < 5 or '.' not in filename:
                filename = f"search_image_{int(time.time())}.jpg"
            
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            print(f"✅ تم حفظ الصورة مؤقتاً: {temp_path}")

            # جلب جميع المنتجات من قاعدة البيانات
            print("🔍 جلب جميع المنتجات من قاعدة البيانات...")
            all_products = db.get_all_products()
            print(f"تم العثور على {len(all_products)} منتج")

            # البحث عن المنتجات التي لها صور
            products_with_images = []
            for product in all_products:
                if product.get('image'):
                    products_with_images.append(product)
            
            print(f"منتجات لها صور: {len(products_with_images)}")

            # البحث عن المنتجات المشابهة باستخدام محرك البحث بالصورة
            matched_products = []
            try:
                # استخراج embedding للصورة المدخلة
                query_embedding = get_image_embedding_clip(temp_path)
                # البحث عن أقرب الصور (ترجع مسارات الصور)
                results = image_search_engine.search(query_embedding, k=10)
                # استخراج أسماء الملفات من المسارات
                result_filenames = [os.path.basename(path) for path in results]
                # جلب جميع المنتجات من قاعدة البيانات
                all_products = db.get_all_products()
                # مطابقة المنتجات التي تملك نفس اسم الصورة
                for product in all_products:
                    if product.get('image') and product['image'] in result_filenames:
                        matched_products.append(product)
                print(f"تم العثور على {len(matched_products)} منتج مشابه فعليًا")
            except Exception as e:
                print(f"❌ خطأ في البحث الدقيق بالصورة: {e}")
                matched_products = []

            # إضافة معلومات المتجر لكل منتج
            for product in matched_products:
                if product.get('store_id'):
                    store = db.get_store_by_id(product['store_id'])
                    if store:
                        product['store_name'] = store.get('name', 'متجر غير معروف')
                    else:
                        product['store_name'] = 'متجر غير معروف'
                else:
                    product['store_name'] = 'متجر غير محدد'

            # حذف الصورة المؤقتة
            try:
                os.remove(temp_path)
                print("✅ تم حذف الصورة المؤقتة")
            except Exception as e:
                print(f"⚠️ تحذير: لم يتم حذف الصورة المؤقتة: {e}")

            # إذا لم يوجد أي منتج، أظهر رسالة
            if not matched_products:
                print("❌ لم يتم العثور على منتجات مشابهة")
                flash('لم يتم العثور على منتجات مشابهة للصورة المدخلة', 'info')
            else:
                print(f"✅ تم العثور على {len(matched_products)} منتج مشابه فعليًا")

            return render_template('search_results.html', 
                                 query="البحث بالصورة",
                                 products=matched_products,
                                 stores=[],  # لا نبحث عن متاجر هنا
                                 search_type='image')  # تحديد نوع البحث
                                 
        except Exception as e:
            print(f"❌ خطأ في معالجة الصورة: {e}")
            import traceback
            print(traceback.format_exc())
            flash('حدث خطأ أثناء معالجة الصورة', 'error')
            return redirect(url_for('home'))
    else:
        print(f"❌ نوع الملف غير مدعوم: {file.filename}")
        flash('نوع الملف غير مدعوم. يرجى استخدام JPG أو PNG', 'warning')
        return redirect(url_for('home'))

@app.route('/search')
def search():
    """البحث عن المنتجات والمتاجر بالاسم"""
    query = request.args.get('q', '').strip()
    
    if not query:
        flash('يرجى إدخال كلمة بحث', 'warning')
        return redirect(url_for('home'))
    
    try:
        # البحث في المنتجات
        products = db.search_products(query)
        
        # البحث في المتاجر
        stores = db.search_stores(query)
        
        print(f"🔍 نتائج البحث عن '{query}':")
        print(f"   - المنتجات: {len(products)}")
        print(f"   - المتاجر: {len(stores)}")
        
        return render_template('search_results.html', 
                             query=query,
                             products=products,
                             stores=stores,
                             search_type='text')  # تحديد نوع البحث
    except Exception as e:
        print(f"خطأ في البحث: {str(e)}")
        flash('حدث خطأ أثناء البحث', 'error')
        return redirect(url_for('home'))

def migrate_old_images():
    """
    نقل الصور القديمة من المجلد العام إلى المجلدات المخصصة
    """
    print("\n=== بدء نقل الصور القديمة ===")
    
    try:
        # التحقق من وجود صور في المجلد العام
        old_upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(old_upload_folder):
            files = os.listdir(old_upload_folder)
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if image_files:
                print(f"تم العثور على {len(image_files)} صورة في المجلد القديم")
                
                for image_file in image_files:
                    old_path = os.path.join(old_upload_folder, image_file)
                    
                    # تحديد نوع المحتوى بناءً على اسم الملف
                    if image_file.startswith('store_'):
                        new_folder = app.config['STORES_UPLOAD_FOLDER']
                        print(f"نقل صورة متجر: {image_file}")
                    elif image_file.startswith('product_'):
                        new_folder = app.config['PRODUCTS_UPLOAD_FOLDER']
                        print(f"نقل صورة منتج: {image_file}")
                    else:
                        # إذا لم نتمكن من تحديد النوع، نتركه في المجلد العام
                        print(f"ترك الصورة في المجلد العام: {image_file}")
                        continue
                    
                    # إنشاء المجلد الجديد إذا لم يكن موجوداً
                    os.makedirs(new_folder, exist_ok=True)
                    
                    # نسخ الملف
                    new_path = os.path.join(new_folder, image_file)
                    if not os.path.exists(new_path):
                        import shutil
                        shutil.copy2(old_path, new_path)
                        print(f"✅ تم نسخ {image_file} إلى {new_folder}")
                    else:
                        print(f"⚠️ الملف موجود بالفعل: {new_path}")
            else:
                print("لم يتم العثور على صور في المجلد القديم")
        else:
            print("المجلد القديم غير موجود")
            
    except Exception as e:
        print(f"خطأ في نقل الصور: {str(e)}")
    
    print("=== انتهى نقل الصور القديمة ===\n")

# تشغيل نقل الصور عند بدء التطبيق
migrate_old_images()

# مسارات إدارة الأقسام للمشرف
@app.route('/admin/categories')
@login_required
def admin_categories():
    """إدارة الأقسام"""
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        print("=== بدء جلب بيانات الأقسام ===")
        
        # جلب الأقسام
        categories = db.get_all_categories()
        print(f"تم جلب {len(categories)} قسم")
        
        # جلب المتاجر والمنتجات لحساب الإحصائيات
        stores = db.get_all_stores()
        products = db.get_all_products()
        
        print(f"تم جلب {len(stores)} متجر و {len(products)} منتج")
        
        # طباعة تفاصيل المتاجر للتشخيص
        print("\n=== تفاصيل المتاجر ===")
        for store in stores:
            print(f"متجر: {store.get('name', 'بدون اسم')} - القسم: {store.get('category', 'غير محدد')}")
        
        # طباعة تفاصيل المنتجات للتشخيص
        print("\n=== تفاصيل المنتجات ===")
        for product in products:
            print(f"منتج: {product.get('name', 'بدون اسم')} - القسم: {product.get('category', 'غير محدد')} - المتجر: {product.get('store_name', 'غير محدد')}")
        
        # حساب إحصائيات كل قسم
        for category in categories:
            category_id = str(category['_id'])
            category_name = category.get('name', '')
            
            print(f"\nحساب إحصائيات القسم: {category_name}")
            
            # حساب عدد المتاجر في هذا القسم
            category_stores = [s for s in stores if s.get('category') == category_name]
            category['stores_count'] = len(category_stores)
            
            # حساب عدد المنتجات في هذا القسم
            category_products = [p for p in products if p.get('category') == category_name]
            category['products_count'] = len(category_products)
            
            print(f"القسم {category_name}: {len(category_stores)} متجر، {len(category_products)} منتج")
            
            # التأكد من وجود صورة للقسم
            if not category.get('image'):
                # استخدام صورة افتراضية حسب نوع القسم
                default_images = {
                    'ملابس رجالية': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&auto=format&fit=crop',
                    'ملابس نسائية': 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=800&auto=format&fit=crop',
                    'أطفال': 'https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800&auto=format&fit=crop',
                    'إلكترونيات': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&auto=format&fit=crop',
                    'هواتف': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&auto=format&fit=crop',
                    'أحذية': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&auto=format&fit=crop'
                }
                category['image'] = default_images.get(category_name, 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&auto=format&fit=crop')
        
        # حساب الإحصائيات العامة
        total_stores = len(stores)
        total_products = len(products)
        
        # تحديد القسم الأكثر شعبية
        most_popular_category = "لا يوجد"
        max_products = 0
        for category in categories:
            if category.get('products_count', 0) > max_products:
                max_products = category.get('products_count', 0)
                most_popular_category = category.get('name', 'غير معروف')
        
        print(f"\n=== الإحصائيات النهائية ===")
        print(f"القسم الأكثر شعبية: {most_popular_category} بـ {max_products} منتج")
        print(f"إجمالي المتاجر: {total_stores}")
        print(f"إجمالي المنتجات: {total_products}")
        
        return render_template('admin/categories.html', 
                             categories=categories,
                             total_stores=total_stores,
                             total_products=total_products,
                             most_popular_category=most_popular_category)
    except Exception as e:
        print(f"خطأ في صفحة إدارة الأقسام: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء جلب البيانات')
        return render_template('error.html', message=str(e))

@app.route('/admin/categories/add', methods=['POST'])
@login_required
def admin_add_category():
    """إضافة قسم جديد"""
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon')
        
        if not all([name, description, icon]):
            flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
            return redirect(url_for('admin_categories'))
        
        # معالجة الصورة
        image_filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                try:
                    original_filename = secure_filename(image_file.filename)
                    image_filename = generate_unique_filename(original_filename, "category")
                    
                    os.makedirs(app.config['CATEGORIES_UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['CATEGORIES_UPLOAD_FOLDER'], image_filename)
                    image_file.save(file_path)
                    print(f"✅ تم حفظ صورة القسم بنجاح: {image_filename}")
                except Exception as e:
                    print(f"❌ حدث خطأ أثناء حفظ صورة القسم: {e}")
                    flash('حدث خطأ أثناء حفظ صورة القسم', 'warning')
        
        # إضافة القسم إلى قاعدة البيانات
        category_data = {
            'name': name,
            'description': description,
            'icon': icon,
            'image': image_filename or DEFAULT_CATEGORY_IMAGES.get(name or '', 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&auto=format&fit=crop')
        }
        
        # إضافة القسم إلى قاعدة البيانات
        if db.db and db.db.categories:
            result = db.db.categories.insert_one(category_data)
            
            if result.inserted_id:
                flash('تم إضافة القسم بنجاح', 'success')
            else:
                flash('حدث خطأ أثناء إضافة القسم', 'danger')
        else:
            flash('لا يمكن الاتصال بقاعدة البيانات', 'danger')
            
        return redirect(url_for('admin_categories'))
    except Exception as e:
        flash('حدث خطأ أثناء إضافة القسم')
        return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<category_id>/edit', methods=['POST'])
@login_required
def admin_edit_category(category_id):
    """تعديل قسم"""
    if current_user.user_type != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon')
        
        if not all([name, description, icon]):
            flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
            return redirect(url_for('admin_categories'))
        
        # معالجة الصورة
        image_filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                try:
                    original_filename = secure_filename(image_file.filename)
                    image_filename = generate_unique_filename(original_filename, "category")
                    
                    os.makedirs(app.config['CATEGORIES_UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['CATEGORIES_UPLOAD_FOLDER'], image_filename)
                    image_file.save(file_path)
                    print(f"✅ تم حفظ صورة القسم بنجاح: {image_filename}")
                except Exception as e:
                    print(f"❌ حدث خطأ أثناء حفظ صورة القسم: {e}")
                    flash('حدث خطأ أثناء حفظ صورة القسم', 'warning')
        
        # تحديث القسم في قاعدة البيانات
        category_data = {
            'name': name,
            'description': description,
            'icon': icon
        }
        
        # إضافة الصورة إذا تم رفعها
        if image_filename:
            category_data['image'] = image_filename
        else:
            # استخدام الصورة الافتراضية إذا لم يتم رفع صورة
            category_data['image'] = DEFAULT_CATEGORY_IMAGES.get(name or '', 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&auto=format&fit=crop')
        
        # تحديث القسم في قاعدة البيانات
        if db.db and db.db.categories:
            result = db.db.categories.update_one(
                {'_id': ObjectId(category_id)},
                {'$set': category_data}
            )
            
            if result.modified_count > 0:
                flash('تم تحديث القسم بنجاح', 'success')
            else:
                flash('لم يتم تحديث أي شيء', 'info')
        else:
            flash('لا يمكن الاتصال بقاعدة البيانات', 'danger')
            
        return redirect(url_for('admin_categories'))
    except Exception as e:
        flash('حدث خطأ أثناء تحديث القسم')
        return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<category_id>/delete', methods=['POST'])
@login_required
def admin_delete_category(category_id):
    """حذف قسم"""
    if current_user.user_type != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'})
    
    try:
        # حذف القسم من قاعدة البيانات
        if db.db and db.db.categories:
            result = db.db.categories.delete_one({'_id': ObjectId(category_id)})
            
            if result.deleted_count > 0:
                return jsonify({'success': True, 'message': 'تم حذف القسم بنجاح'})
            else:
                return jsonify({'success': False, 'message': 'لم يتم العثور على القسم'})
        else:
            return jsonify({'success': False, 'message': 'لا يمكن الاتصال بقاعدة البيانات'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """صفحة الإحصائيات التفصيلية للمشرف"""
    if current_user.user_type != 'admin':
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        print("=== بدء حساب الإحصائيات التفصيلية ===")
        
        # إحصائيات المستخدمين
        users = db.get_all_users()
        total_users = len(users)
        admin_users = len([u for u in users if u['user_type'] == 'admin'])
        store_users = len([u for u in users if u['user_type'] == 'store_owner'])
        customer_users = len([u for u in users if u['user_type'] == 'customer'])
        
        print(f"إحصائيات المستخدمين: إجمالي {total_users}, مشرفين {admin_users}, متاجر {store_users}, عملاء {customer_users}")
        
        # حساب النسب المئوية للمستخدمين
        admin_percentage = (admin_users / total_users * 100) if total_users > 0 else 0
        store_percentage = (store_users / total_users * 100) if total_users > 0 else 0
        customer_percentage = (customer_users / total_users * 100) if total_users > 0 else 0
        
        # إحصائيات المتاجر
        stores = db.get_all_stores()
        total_stores = len(stores)
        print(f"إجمالي المتاجر: {total_stores}")
        
        # إحصائيات المنتجات
        products = db.get_all_products()
        total_products = len(products)
        print(f"إجمالي المنتجات: {total_products}")
        
        # إحصائيات الطلبات
        orders = db.get_all_orders()
        total_orders = len(orders)
        pending_orders = len([o for o in orders if o.get('status') == 'pending'])
        completed_orders = len([o for o in orders if o.get('status') == 'completed'])
        cancelled_orders = len([o for o in orders if o.get('status') == 'cancelled'])
        
        print(f"إحصائيات الطلبات: إجمالي {total_orders}, معلق {pending_orders}, مكتمل {completed_orders}, ملغي {cancelled_orders}")
        
        # حساب النسب المئوية للطلبات
        pending_percentage = (pending_orders / total_orders * 100) if total_orders > 0 else 0
        completed_percentage = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        cancelled_percentage = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
        
        # حساب إجمالي الإيرادات
        total_revenue = sum([float(o.get('total', 0)) for o in orders if o.get('status') == 'completed'])
        print(f"إجمالي الإيرادات: {total_revenue} ريال")
        
        # إحصائيات الأقسام
        categories = db.get_all_categories()
        total_categories = len(categories)
        categories_stats = []
        
        print("حساب إحصائيات الأقسام:")
        for category in categories:
            category_name = category.get('name', '')
            category_products = [p for p in products if p.get('category') == category_name]
            products_count = len(category_products)
            
            # حساب النسبة المئوية
            percentage = (products_count / total_products * 100) if total_products > 0 else 0
            
            print(f"القسم {category_name}: {products_count} منتج ({percentage:.1f}%)")
            
            categories_stats.append({
                'name': category_name,
                'products_count': products_count,
                'percentage': percentage
            })
        
        # أفضل المتاجر أداءً
        top_stores = []
        print("حساب أفضل المتاجر أداءً:")
        
        for store in stores:
            store_name = store.get('name', '')
            store_products = [p for p in products if p.get('store_id') == str(store['_id'])]
            products_count = len(store_products)
            
            # حساب الطلبات التي تحتوي على منتجات من هذا المتجر
            store_orders = []
            for order in orders:
                if order.get('order_items'):
                    for item in order.get('order_items', []):
                        # البحث عن المنتج في الطلب
                        for product in store_products:
                            if product.get('name') == item.get('name'):
                                store_orders.append(order)
                                break
            
            # حساب إيرادات المتجر
            store_revenue = sum([float(o.get('total', 0)) for o in store_orders if o.get('status') == 'completed'])
            
            print(f"المتجر {store_name}: {products_count} منتج، {len(store_orders)} طلب، {store_revenue} ريال إيرادات")
            
            top_stores.append({
                'name': store_name,
                'products_count': products_count,
                'orders_count': len(store_orders),
                'revenue': int(store_revenue)
            })
        
        # ترتيب المتاجر حسب الإيرادات
        top_stores.sort(key=lambda x: x['revenue'], reverse=True)
        top_stores = top_stores[:5]  # أفضل 5 متاجر
        
        print("أفضل 5 متاجر:")
        for i, store in enumerate(top_stores, 1):
            print(f"{i}. {store['name']}: {store['revenue']} ريال")
        
        return render_template('admin/analytics.html',
                             total_users=total_users,
                             total_stores=total_stores,
                             total_products=total_products,
                             total_orders=total_orders,
                             total_revenue=int(total_revenue),
                             total_categories=total_categories,
                             
                             # إحصائيات المستخدمين
                             admin_users=admin_users,
                             store_users=store_users,
                             customer_users=customer_users,
                             admin_percentage=admin_percentage,
                             store_percentage=store_percentage,
                             customer_percentage=customer_percentage,
                             
                             # إحصائيات الطلبات
                             pending_orders=pending_orders,
                             completed_orders=completed_orders,
                             cancelled_orders=cancelled_orders,
                             pending_percentage=pending_percentage,
                             completed_percentage=completed_percentage,
                             cancelled_percentage=cancelled_percentage,
                             
                             # إحصائيات الأقسام والمتاجر
                             categories_stats=categories_stats,
                             top_stores=top_stores)
    
    except Exception as e:
        print(f"خطأ في صفحة الإحصائيات: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء تحميل الإحصائيات', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/stores')
@login_required
def admin_stores():
    print("\n=== محاولة الوصول إلى صفحة المتاجر ===")
    print(f"نوع المستخدم الحالي: {current_user.user_type}")
    
    if not current_user.is_authenticated or current_user.user_type != 'admin':
        print("خطأ: المستخدم غير مصرح له بالوصول")
        flash('يجب تسجيل الدخول كمشرف للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        # التحقق من الاتصال بقاعدة البيانات
        if not db.ensure_connection():
            print("خطأ: لا يمكن الاتصال بقاعدة البيانات")
            flash('حدث خطأ في الاتصال بقاعدة البيانات', 'danger')
            return render_template('admin/stores.html', stores=[])
        
        # جلب المتاجر
        print("جاري جلب المتاجر...")
        stores = db.get_all_stores()
        
        if stores is None:
            print("تم استلام None من قاعدة البيانات")
            stores = []
        elif not isinstance(stores, list):
            print(f"تم استلام نوع بيانات غير متوقع: {type(stores)}")
            stores = []
            
        print(f"تم جلب {len(stores)} متجر")
        
        if not stores:
            print("لم يتم العثور على متاجر")
            flash('لا توجد متاجر في النظام', 'info')
        else:
            print(f"تم العثور على {len(stores)} متجر")
            for store in stores:
                print(f"متجر: {store.get('name', 'بدون اسم')} - {store.get('_id', 'بدون معرف')}")
        
        return render_template('admin/stores.html', stores=stores)
        
    except Exception as e:
        print(f"خطأ في جلب المتاجر: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('حدث خطأ أثناء جلب البيانات', 'danger')
        return render_template('admin/stores.html', stores=[])

if __name__ == '__main__':
    print("\n=== بدء تشغيل التطبيق ===")
    
    # التحقق من حالة قاعدة البيانات
    if not db.is_connected():
        print("⚠️ تحذير: لم يتم الاتصال بقاعدة البيانات. سيتم تشغيل التطبيق في وضع العرض فقط")
        print("تأكد من:")
        print("1. صحة معلومات الاتصال بقاعدة البيانات")
        print("2. وجود اتصال بالإنترنت")
        print("3. صحة رابط MongoDB")
    else:
        print("✅ تم الاتصال بقاعدة البيانات بنجاح")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {str(e)}")
        import traceback
        print(traceback.format_exc()) 