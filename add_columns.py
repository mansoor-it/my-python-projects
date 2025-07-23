import sqlite3

def add_columns():
    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect('ecommerce.db')  # استبدل 'your_database.db' باسم قاعدة البيانات الخاصة بك
    cursor = conn.cursor()

    # إضافة الأعمدة إلى جدول deposits
    cursor.execute('ALTER TABLE deposits ADD COLUMN deposit_date TEXT')
    cursor.execute('ALTER TABLE deposits ADD COLUMN deposit_time TEXT')

    # تأكيد التغييرات
    conn.commit()
    print("تمت إضافة الأعمدة deposit_date و deposit_time بنجاح.")
    
    # إغلاق الاتصال
    conn.close()

if __name__ == '__main__':
    add_columns()