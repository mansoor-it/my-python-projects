# # test_ecommerce_db.py
import unittest  # استيراد مكتبة اختبار الوحدات
import sqlite3  # استيراد مكتبة التعامل مع قواعد بيانات SQLite
import os  # استيراد مكتبة العمليات المتعلقة بالنظام

DB_PATH = 'ecommerce.db'  # مسار قاعدة البيانات

class TestEcommerceDB(unittest.TestCase):  # تعريف كلاس لاختبارات قاعدة بيانات التجارة الإلكترونية

    def setUp(self):  # إعداد الاتصال بقاعدة البيانات قبل كل اختبار
        # تأكد أن الملف موجود
        if not os.path.exists(DB_PATH):  # التحقق من وجود ملف قاعدة البيانات
            self.fail(f"Database file {DB_PATH} does not exist.")  # إيقاف الاختبار إذا لم توجد القاعدة
        self.conn = sqlite3.connect(DB_PATH)  # فتح اتصال بقاعدة البيانات
        self.cursor = self.conn.cursor()  # إنشاء المؤشر للتنفيذ على قاعدة البيانات

    def tearDown(self):  # إغلاق الاتصال بعد كل اختبار
        self.conn.close()  # إغلاق الاتصال بقاعدة البيانات

    def test_insert_user(self):  # اختبار إدخال مستخدم جديد
        try:
            self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",  # تنفيذ أمر إدخال مستخدم
                                ("testuser", "test_new@example.com", "test123"))  # بيانات المستخدم
            self.conn.commit()  # حفظ التغييرات

            self.cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))  # جلب المستخدم للتأكد من إضافته
            result = self.cursor.fetchone()  # الحصول على النتيجة
            self.assertIsNotNone(result)  # التأكد من أن النتيجة غير فارغة (أي تم الإدخال)
        finally:
            self.cursor.execute("DELETE FROM users WHERE username = ?", ("testuser",))  # حذف المستخدم بعد الاختبار
            self.conn.commit()  # حفظ التغييرات

    def test_insert_product(self):  # اختبار إدخال منتج جديد
        try:
            self.cursor.execute("INSERT INTO products (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)",  # تنفيذ أمر إدخال منتج
                                ("Test Product", 123.45, "Test Desc", 3, "test.jpg"))  # بيانات المنتج
            self.conn.commit()  # حفظ التغييرات

            self.cursor.execute("SELECT * FROM products WHERE name = ?", ("Test Product",))  # جلب المنتج للتأكد من إضافته
            result = self.cursor.fetchone()  # الحصول على النتيجة
            self.assertIsNotNone(result)  # التأكد من أن النتيجة غير فارغة
        finally:
            self.cursor.execute("DELETE FROM products WHERE name = ?", ("Test Product",))  # حذف المنتج بعد الاختبار
            self.conn.commit()  # حفظ التغييرات

    def test_add_to_cart(self):  # اختبار إضافة منتج إلى سلة المشتريات
        try:
            # إضافة مستخدم ومنتج (افتراضي)
            self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",  # إدخال مستخدم للاختبار
                                ("cartuser", "cart@example.com", "pass"))
            self.cursor.execute("INSERT INTO products (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)",  # إدخال منتج للاختبار
                                ("Cart Product", 55.55, "For cart test", 5, "cart.jpg"))
            self.conn.commit()  # حفظ التغييرات

            # جلب IDs
            self.cursor.execute("SELECT id FROM users WHERE username = ?", ("cartuser",))  # جلب id المستخدم
            user_id = self.cursor.fetchone()[0]  # استخراج قيمة id
            self.cursor.execute("SELECT id FROM products WHERE name = ?", ("Cart Product",))  # جلب id المنتج
            product_id = self.cursor.fetchone()[0]  # استخراج قيمة id

            # إضافة إلى السلة
            self.cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",  # إدخال المنتج إلى السلة
                                (user_id, product_id, 2))
            self.conn.commit()  # حفظ التغييرات

            # تحقق
            self.cursor.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))  # التحقق من وجود السجل في السلة
            result = self.cursor.fetchone()  # جلب النتيجة
            self.assertIsNotNone(result)  # التأكد من أن السجل أُضيف فعلاً
        finally:
            # تنظيف البيانات بعد الاختبار
            self.cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))  # حذف المنتج من السلة
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))  # حذف المستخدم
            self.cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))  # حذف المنتج
            self.conn.commit()  # حفظ التغييرات

if __name__ == '__main__':  # تشغيل الاختبارات إن كان الملف هو الملف الرئيسي
    unittest.main()  # تشغيل اختبارات الوحدة

# import unittest
# import sqlite3
# import os

# DB_PATH = 'ecommerce.db'

# class TestEcommerceDB(unittest.TestCase):

#     def setUp(self):
#         # تأكد أن الملف موجود
#         if not os.path.exists(DB_PATH):
#             self.fail(f"Database file {DB_PATH} does not exist.")
#         self.conn = sqlite3.connect(DB_PATH)
#         self.cursor = self.conn.cursor()

#     def tearDown(self):
#         self.conn.close()

#     def test_insert_user(self):
#         try:
#             self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
#                                 ("testuser", "test_new@example.com", "test123"))
#             self.conn.commit()

#             self.cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
#             result = self.cursor.fetchone()
#             self.assertIsNotNone(result)
#         finally:
#             self.cursor.execute("DELETE FROM users WHERE username = ?", ("testuser",))
#             self.conn.commit()

#     def test_insert_product(self):
#         try:
#             self.cursor.execute("INSERT INTO products (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)",
#                                 ("Test Product", 123.45, "Test Desc", 3, "test.jpg"))
#             self.conn.commit()

#             self.cursor.execute("SELECT * FROM products WHERE name = ?", ("Test Product",))
#             result = self.cursor.fetchone()
#             self.assertIsNotNone(result)
#         finally:
#             self.cursor.execute("DELETE FROM products WHERE name = ?", ("Test Product",))
#             self.conn.commit()

#     def test_add_to_cart(self):
#         try:
#             # إضافة مستخدم ومنتج (افتراضي)
#             self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
#                                 ("cartuser", "cart@example.com", "pass"))
#             self.cursor.execute("INSERT INTO products (name, price, description, quantity, image_url) VALUES (?, ?, ?, ?, ?)",
#                                 ("Cart Product", 55.55, "For cart test", 5, "cart.jpg"))
#             self.conn.commit()

#             # جلب IDs
#             self.cursor.execute("SELECT id FROM users WHERE username = ?", ("cartuser",))
#             user_id = self.cursor.fetchone()[0]
#             self.cursor.execute("SELECT id FROM products WHERE name = ?", ("Cart Product",))
#             product_id = self.cursor.fetchone()[0]

#             # إضافة إلى السلة
#             self.cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
#                                 (user_id, product_id, 2))
#             self.conn.commit()

#             # تحقق
#             self.cursor.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
#             result = self.cursor.fetchone()
#             self.assertIsNotNone(result)
#         finally:
#             # تنظيف البيانات بعد الاختبار
#             self.cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
#             self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
#             self.cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
#             self.conn.commit()

# if __name__ == '__main__':
#     unittest.main()
