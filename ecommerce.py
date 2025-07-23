import sqlite3

# إنشاء قاعدة بيانات جديدة أو الاتصال بقاعدة بيانات موجودة
conn = sqlite3.connect('ecommerce.db')

# إنشاء كائن المؤشر
cursor = conn.cursor()

# إنشاء جدول المنتجات مع عمود الصورة
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    image_url TEXT  -- إضافة عمود الصورة
)
''')
# إنشاء جدول الأدوات المنزلية
cursor.execute('''
CREATE TABLE IF NOT EXISTS home_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    image_url TEXT  -- إضافة عمود الصورة
)
''')
# إنشاء جدول للتعليقات
cursor.execute('''
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# إنشاء جدول السلة
cursor.execute('''
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
)
''')

# إنشاء جدول الطلبات
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    order_date TEXT,
    total REAL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# إنشاء جدول المستخدمين
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("Database and tables created/updated successfully.")