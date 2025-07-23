import unittest  # مكتبة لاختبار وحدات البرامج (Unit Testing)
import sqlite3   # مكتبة للتعامل مع قواعد بيانات SQLite
import os        # مكتبة للتعامل مع الملفات والمجلدات

DB_PATH = 'ecommerce.db'  # مسار ملف قاعدة البيانات

class TestEcommerceDB(unittest.TestCase):  # تعريف كلاس يحتوي على اختبارات قاعدة بيانات المستخدمين

    def setUp(self):  # دالة يتم تنفيذها قبل كل اختبار
        # تأكد أن الملف موجود
        if not os.path.exists(DB_PATH):  # إذا لم يكن ملف قاعدة البيانات موجودًا
            self.fail(f"Database file {DB_PATH} does not exist.")  # فشل الاختبار مع رسالة توضح المشكلة
        self.conn = sqlite3.connect(DB_PATH)  # فتح اتصال بقاعدة البيانات
        self.cursor = self.conn.cursor()  # إنشاء كائن Cursor لتنفيذ الاستعلامات

    def tearDown(self):  # دالة يتم تنفيذها بعد كل اختبار
        self.conn.close()  # إغلاق الاتصال بقاعدة البيانات

    def test_insert_user(self):  # اختبار عملية إدخال مستخدم جديد
        try:
            # إدخال مستخدم جديد
            self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                                ("testuser", "test@ehxample.com", "test123"))  # تنفيذ استعلام الإدخال
            self.conn.commit()  # حفظ التغييرات في قاعدة البيانات

            # التحقق من وجود المستخدم في قاعدة البيانات
            self.cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))  # استعلام بحث
            result = self.cursor.fetchone()  # الحصول على أول نتيجة
            self.assertIsNotNone(result)  # التأكد أن المستخدم تم إيجاده
            self.assertEqual(result[1], "testuser")  # التحقق أن اسم المستخدم في النتيجة مطابق
        finally:
            self.cursor.execute("DELETE FROM users WHERE username = ?", ("testuser",))  # حذف المستخدم بعد الاختبار
            self.conn.commit()  # حفظ التغييرات

    def test_update_user(self):  # اختبار تعديل بيانات مستخدم
        try:
            # إضافة مستخدم لتعديله لاحقًا
            self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                                ("updateuser", "update@example.com", "update123"))  # إدخال مستخدم
            self.conn.commit()  # حفظ التغييرات

            # تحديث اسم المستخدم
            self.cursor.execute("UPDATE users SET username = ? WHERE username = ?", ("updateduser", "updateuser"))  # تعديل الاسم
            self.conn.commit()  # حفظ التعديلات

            # التحقق من التحديث
            self.cursor.execute("SELECT * FROM users WHERE username = ?", ("updateduser",))  # استعلام للتحقق من التحديث
            result = self.cursor.fetchone()  # الحصول على النتيجة
            self.assertIsNotNone(result)  # التأكد أن المستخدم موجود
            self.assertEqual(result[1], "updateduser")  # التأكد أن الاسم الجديد صحيح
        finally:
            self.cursor.execute("DELETE FROM users WHERE username = ?", ("updateduser",))  # حذف المستخدم
            self.conn.commit()  # حفظ التغييرات

    def test_delete_user(self):  # اختبار حذف مستخدم
        try:
            # إضافة مستخدم لحذفه لاحقًا
            self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                                ("deleteuser", "delete@example.com", "delete123"))  # إدخال المستخدم
            self.conn.commit()  # حفظ التغييرات

            # حذف المستخدم
            self.cursor.execute("DELETE FROM users WHERE username = ?", ("deleteuser",))  # تنفيذ الحذف
            self.conn.commit()  # حفظ التغييرات

            # التحقق من الحذف
            self.cursor.execute("SELECT * FROM users WHERE username = ?", ("deleteuser",))  # محاولة إيجاده
            result = self.cursor.fetchone()  # جلب النتيجة
            self.assertIsNone(result)  # يجب ألا يكون موجودًا (يجب أن تكون النتيجة None)
        finally:
            self.conn.commit()  # حفظ التغييرات (احتياطيًا)

    def test_select_user_by_email(self):  # اختبار استعلام مستخدم عبر البريد الإلكتروني
        try:
            # إدخال مستخدم لاختباره بالبحث عبر البريد الإلكتروني
            self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                                ("emailuser", "email@example.com", "email123"))  # إدخال مستخدم
            self.conn.commit()  # حفظ التغييرات

            # البحث عن المستخدم باستخدام البريد الإلكتروني
            self.cursor.execute("SELECT * FROM users WHERE email = ?", ("email@example.com",))  # تنفيذ استعلام
            result = self.cursor.fetchone()  # جلب النتيجة
            self.assertIsNotNone(result)  # التحقق من أن النتيجة ليست فارغة
            self.assertEqual(result[2], "email@example.com")  # التحقق من صحة البريد الإلكتروني في النتيجة
        finally:
            self.cursor.execute("DELETE FROM users WHERE email = ?", ("email@example.com",))  # حذف المستخدم بعد الاختبار
            self.conn.commit()  # حفظ التغييرات

if __name__ == '__main__':  # تنفيذ هذه الكتلة فقط إذا شغلت الملف مباشرة
    unittest.main()  # تشغيل جميع الاختبارات المعرفة في الكلاس

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
#             # إدخال مستخدم جديد
#             self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
#                                 ("testuser", "test@example.com", "test123"))
#             self.conn.commit()

#             # التحقق من وجود المستخدم في قاعدة البيانات
#             self.cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
#             result = self.cursor.fetchone()
#             self.assertIsNotNone(result)
#             self.assertEqual(result[1], "testuser")  # username هو العمود الثاني في الجدول
#         finally:
#             self.cursor.execute("DELETE FROM users WHERE username = ?", ("testuser",))
#             self.conn.commit()

#     def test_update_user(self):
#         try:
#             # إضافة مستخدم لتعديله لاحقًا
#             self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
#                                 ("updateuser", "update@example.com", "update123"))
#             self.conn.commit()

#             # تحديث اسم المستخدم
#             self.cursor.execute("UPDATE users SET username = ? WHERE username = ?", ("updateduser", "updateuser"))
#             self.conn.commit()

#             # التحقق من التحديث
#             self.cursor.execute("SELECT * FROM users WHERE username = ?", ("updateduser",))
#             result = self.cursor.fetchone()
#             self.assertIsNotNone(result)
#             self.assertEqual(result[1], "updateduser")
#         finally:
#             self.cursor.execute("DELETE FROM users WHERE username = ?", ("updateduser",))
#             self.conn.commit()

#     def test_delete_user(self):
#         try:
#             # إضافة مستخدم لحذفه لاحقًا
#             self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
#                                 ("deleteuser", "delete@example.com", "delete123"))
#             self.conn.commit()

#             # حذف المستخدم
#             self.cursor.execute("DELETE FROM users WHERE username = ?", ("deleteuser",))
#             self.conn.commit()

#             # التحقق من الحذف
#             self.cursor.execute("SELECT * FROM users WHERE username = ?", ("deleteuser",))
#             result = self.cursor.fetchone()
#             self.assertIsNone(result)
#         finally:
#             self.conn.commit()

#     def test_select_user_by_email(self):
#         try:
#             # إدخال مستخدم لاختباره بالبحث عبر البريد الإلكتروني
#             self.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
#                                 ("emailuser", "email@example.com", "email123"))
#             self.conn.commit()

#             # البحث عن المستخدم باستخدام البريد الإلكتروني
#             self.cursor.execute("SELECT * FROM users WHERE email = ?", ("email@example.com",))
#             result = self.cursor.fetchone()
#             self.assertIsNotNone(result)
#             self.assertEqual(result[2], "email@example.com")  # email هو العمود الثالث في الجدول
#         finally:
#             self.cursor.execute("DELETE FROM users WHERE email = ?", ("email@example.com",))
#             self.conn.commit()

# if __name__ == '__main__':
#     unittest.main()
