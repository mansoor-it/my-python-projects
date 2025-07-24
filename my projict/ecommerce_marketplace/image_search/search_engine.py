import os
import numpy as np
from image_search.vectorizer import get_image_embedding_clip

class ImageSearchEngine:
    def __init__(self, images_folder: str):
        """
        images_folder: المسار إلى الجذر الذي يحتوي على جميع الصور (png و jpg) 
                       مثل "static/uploads".
        """
        # استخدام المسار الممرر بدلاً من حساب المسار
        self.images_folder = images_folder
        self.image_paths = []
        self.embeddings = None

    def build_index(self):
        """
        يقرأ جميع الصور (.jpg/.jpeg/.png) ضمن جميع المجلدات الفرعية في self.images_folder،
        يحسب embedding لكل صورة.
        """
        all_embeddings = []
        
        # التأكد من وجود المجلد
        os.makedirs(self.images_folder, exist_ok=True)
        
        # استخدم os.walk ليزور المجلد والفرعيّات بحثًا عن ملفات الصور
        for root, dirs, files in os.walk(self.images_folder):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    full_path = os.path.join(root, filename)
                    self.image_paths.append(full_path)
                    try:
                        emb = get_image_embedding_clip(full_path)
                        all_embeddings.append(emb)
                    except Exception as e:
                        print(f"⚠️ فشل استخراج embedding من الصورة {full_path}: {e}")

        if not all_embeddings:
            print(f"تحذير: لم نعثر على أي صور في {self.images_folder} أو مجلداته الفرعية.")
            # إنشاء مصفوفة فارغة بدلاً من رفع استثناء
            self.embeddings = np.zeros((0, 512), dtype='float32')
            return

        self.embeddings = np.array(all_embeddings).astype('float32')
        
        # فحص إضافي للتأكد من أن المصفوفة ليست فارغة
        if self.embeddings.shape[0] == 0:
            print(f"تحذير: لم نتمكن من استخراج embeddings من الصور في {self.images_folder}")
            self.embeddings = np.zeros((0, 512), dtype='float32')
            return
            
        print(f"✅ تم بناء مؤشر البحث لعدد {len(self.image_paths)} صورة في '{self.images_folder}' وكل مجلداته الفرعية.")

    def search(self, query_embedding: np.ndarray, k: int = 5):
        """
        يبحث عن k أقرب صور باستخدام مسافة L2 (Euclidean).
        يُرجع قائمة بمسارات الصور المشابهة.
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []  # إرجاع قائمة فارغة إذا لم تكن هناك صور
        
        try:
            # حساب المسافات بين query_embedding وجميع الصور
            query_vec = np.array(query_embedding).astype('float32')
            distances = np.linalg.norm(self.embeddings - query_vec, axis=1)
            
            # الحصول على أقرب k صور
            k = min(k, len(self.image_paths))
            if k == 0:
                return []
                
            # ترتيب المسافات والحصول على المؤشرات
            indices = np.argsort(distances)[:k]
            
            # إرجاع مسارات الصور
            results = [self.image_paths[idx] for idx in indices if idx < len(self.image_paths)]
            return results
        except Exception as e:
            print(f"خطأ في البحث: {e}")
            return []
