import sqlite3

# إنشاء قاعدة بيانات جديدة أو الاتصال بقاعدة بيانات موجودة
conn = sqlite3.connect('ecommerce.db')


cursor = conn.cursor()


# إنشاء جدول لتخزين تصويتات المستخدمين
cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                comment_id INTEGER NOT NULL,
                vote_type TEXT NOT NULL,
                UNIQUE(user_id, comment_id)
            );
        ''')

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("Table 'home_tools' created successfully.")
