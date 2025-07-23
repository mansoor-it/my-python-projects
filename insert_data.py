import sqlite3

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('ecommerce.db')

# إنشاء كائن المؤشر
cursor = conn.cursor()
# إضافة عمود access_token إلى جدول users
#cursor.execute('ALTER TABLE users ADD COLUMN access_token TEXT;')
# إضافة بيانات إلى جدول الأدوات المنزلية
home_tools_data = [
    ("مقلاة غير لاصقة", 25.99, "مقلاة عالية الجودة غير لاصقة مع طبقة مضادة للخدش.", 50, "https://example.com/images/pan.jpg"),
    ("مكنسة كهربائية", 199.99, "مكنسة كهربائية بقوة شفط عالية وفلاتر HEPA.", 30, "https://example.com/images/vacuum.jpg"),
    ("خلاط كهربائي", 49.99, "خلاط كهربائي متعدد الوظائف مع شفرات من الفولاذ المقاوم للصدأ.", 70, "https://example.com/images/blender.jpg"),
    ("ماكينة صنع القهوة", 79.99, "ماكينة صنع القهوة الأوتوماتيكية مع تحكم في درجة الحرارة.", 20, "https://example.com/images/coffee_maker.jpg"),
    ("مجفف شعر", 29.99, "مجفف شعر احترافي مع تقنية الأيونات السالبة.", 40, "https://example.com/images/hair_dryer.jpg")
]

# إدخال البيانات إلى جدول الأدوات المنزلية
cursor.executemany('''
ALTER TABLE users ADD COLUMN access_token TEXT;


# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("Data inserted into 'home_tools' table successfully.")
