import sqlite3

def fetch_image_urls():
    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect('ecommerce.db')  # استبدل 'your_database.db' باسم قاعدة البيانات الخاصة بك
    cursor = conn.cursor()

    try:
        # تنفيذ استعلام SELECT
        cursor.execute("SELECT * FROM products WHERE image_url LIKE 'static/images/ma.jpg'")
        rows = cursor.fetchall()  # استرجاع جميع النتائج

        # طباعة النتائج
        if rows:  # إذا كانت هناك نتائج
            for row in rows:
                print(row)  # طباعة كل سجل
        else:
            print("لا توجد سجلات تطابق الشرط.")
    except sqlite3.Error as e:
        print(f"حدث خطأ: {e}")
    finally:
        # إغلاق الاتصال
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fetch_image_urls()