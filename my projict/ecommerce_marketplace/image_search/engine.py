# محرك البحث بالصورة المبسط
import os
from .vectorizer import get_image_hash, compare_images

class SimpleImageSearchEngine:
    def __init__(self, images_folder):
        self.images_folder = images_folder
        self.image_hashes = {}
        self._build_index()
    
    def _build_index(self):
        """بناء فهرس للصور الموجودة"""
        if not os.path.exists(self.images_folder):
            print(f"المجلد {self.images_folder} غير موجود")
            return
        
        print(f"جاري بناء فهرس الصور من {self.images_folder}")
        
        for filename in os.listdir(self.images_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                filepath = os.path.join(self.images_folder, filename)
                try:
                    hash_value = get_image_hash(filepath)
                    if hash_value:
                        self.image_hashes[filename] = hash_value
                except Exception as e:
                    print(f"خطأ في معالجة الصورة {filename}: {e}")
        
        print(f"تم فهرسة {len(self.image_hashes)} صورة")
    
    def search(self, query_hash, k=5):
        """البحث عن الصور المشابهة"""
        if not query_hash:
            return []
        
        results = []
        
        for filename, hash_value in self.image_hashes.items():
            similarity = compare_images(query_hash, hash_value)
            if similarity > 0.7:  # عتبة التشابه
                results.append({
                    'filename': filename,
                    'similarity': similarity,
                    'path': os.path.join(self.images_folder, filename)
                })
        
        # ترتيب النتائج حسب التشابه
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # إرجاع أفضل k نتيجة
        return [r['path'] for r in results[:k]]
    
    def add_image(self, image_path):
        """إضافة صورة جديدة للفهرس"""
        if os.path.exists(image_path):
            filename = os.path.basename(image_path)
            hash_value = get_image_hash(image_path)
            if hash_value:
                self.image_hashes[filename] = hash_value
                print(f"تم إضافة الصورة {filename} للفهرس")
                return True
        return False

# إنشاء نسخة افتراضية من محرك البحث
def create_search_engine(upload_folder):
    """إنشاء محرك بحث للصور في مجلد التحميل"""
    return SimpleImageSearchEngine(upload_folder) 