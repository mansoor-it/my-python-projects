#!/usr/bin/env python3
"""
سكريبت لإنشاء مجلدات الصور يدوياً
"""

import os
import sys

def create_upload_folders():
    """إنشاء جميع مجلدات الصور المطلوبة"""
    
    print("=== إنشاء مجلدات الصور ===")
    
    # المسار الأساسي للمشروع
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # مجلدات الصور
    folders = [
        os.path.join(base_path, 'static', 'uploads'),
        os.path.join(base_path, 'static', 'uploads', 'jpg'),
        os.path.join(base_path, 'static', 'uploads', 'png'),
    ]
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"✅ تم إنشاء/تأكيد المجلد: {folder}")
        except Exception as e:
            print(f"❌ خطأ في إنشاء المجلد {folder}: {e}")
            return False
    
    print("\n=== اختبار الصلاحيات ===")
    
    # اختبار الصلاحيات
    for folder in folders:
        try:
            # محاولة إنشاء ملف تجريبي
            test_file = os.path.join(folder, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✅ صلاحيات صحيحة: {folder}")
        except Exception as e:
            print(f"❌ مشكلة في الصلاحيات: {folder}")
            print(f"   الخطأ: {e}")
            return False
    
    print("\n🎉 تم إنشاء جميع المجلدات بنجاح!")
    return True

if __name__ == "__main__":
    success = create_upload_folders()
    if success:
        print("\nيمكنك الآن تشغيل التطبيق:")
        print("py app.py")
    else:
        print("\n⚠️ هناك مشاكل في الصلاحيات.")
        print("جرب تشغيل PowerShell كمسؤول وإعادة تشغيل السكريبت.")
        sys.exit(1) 