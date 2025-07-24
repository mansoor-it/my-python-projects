# نسخة مبسطة من البحث بالصورة بدون PyTorch

import os
from PIL import Image
import hashlib
import numpy as np
import torch
import open_clip

# تحميل نموذج CLIP مرة واحدة فقط (singleton)
_clip_model = None
_clip_preprocess = None
_clip_device = "cuda" if torch.cuda.is_available() else "cpu"

def load_clip_model():
    global _clip_model, _clip_preprocess
    if _clip_model is None or _clip_preprocess is None:
        print("\n=== تحميل نموذج CLIP ... ===")
        _clip_model, _, _clip_preprocess = open_clip.create_model_and_transforms(
            'ViT-B-32', pretrained='openai', device=_clip_device
        )
        _clip_model.eval()
        print("✅ تم تحميل نموذج CLIP")
    return _clip_model, _clip_preprocess

def get_image_embedding_clip(image_input):
    """
    استخراج embedding عميق للصورة باستخدام CLIP
    يمكن أن يكون image_input مسار ملف أو كائن PIL Image
    """
    try:
        model, preprocess = load_clip_model()
        if isinstance(image_input, str):
            image = Image.open(image_input).convert('RGB')
        elif isinstance(image_input, Image.Image):
            image = image_input.convert('RGB')
        else:
            return np.zeros(512, dtype='float32')
        image_tensor = preprocess(image).unsqueeze(0).to(_clip_device)
        with torch.no_grad():
            image_features = model.encode_image(image_tensor)
            image_features = image_features.cpu().numpy().flatten()
        # تطبيع embedding
        image_features = image_features / np.linalg.norm(image_features)
        return image_features.astype('float32')
    except Exception as e:
        print(f"خطأ في استخراج embedding العميق للصورة: {e}")
        return np.zeros(512, dtype='float32')

def get_image_hash(image_input):
    """
    يحسب hash بسيط للصورة للمقارنة
    يمكن أن يكون image_input مسار ملف أو كائن PIL Image
    """
    try:
        # إذا كان مسار ملف، افتح الصورة
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            return None
        
        # تحويل الصورة إلى حجم صغير للمقارنة
        image = image.resize((8, 8)).convert('L')
        
        # حساب hash بسيط
        pixels = list(image.getdata())
        avg_pixel = sum(pixels) / len(pixels)
        
        # إنشاء hash من البكسل
        hash_value = ''
        for pixel in pixels:
            if pixel > avg_pixel:
                hash_value += '1'
            else:
                hash_value += '0'
        
        return hash_value
        
    except Exception as e:
        print(f"خطأ في حساب hash الصورة: {e}")
        return None

def compare_images(hash1, hash2):
    """
    يقارن بين hash صورتين ويعيد نسبة التشابه
    """
    if not hash1 or not hash2:
        return 0
    
    if len(hash1) != len(hash2):
        return 0
    
    # حساب عدد البتات المختلفة
    differences = sum(1 for a, b in zip(hash1, hash2) if a != b)
    
    # حساب نسبة التشابه
    similarity = 1 - (differences / len(hash1))
    return similarity

def get_image_embedding(image_input):
    """
    يحسب embedding بسيط للصورة (مصفوفة أرقام)
    يمكن أن يكون image_input مسار ملف أو كائن PIL Image
    """
    try:
        # إذا كان مسار ملف، افتح الصورة
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            # إرجاع مصفوفة فارغة إذا فشل فتح الصورة
            return np.zeros(512, dtype='float32')
        
        # تحويل الصورة إلى حجم صغير للمقارنة
        image = image.resize((16, 32)).convert('L')  # 16x32 = 512 بكسل
        
        # تحويل البكسل إلى مصفوفة
        pixels = list(image.getdata())
        
        # التأكد من أن لدينا 512 بكسل
        if len(pixels) < 512:
            # إضافة أصفار إذا كان عدد البكسل أقل من 512
            pixels.extend([0] * (512 - len(pixels)))
        elif len(pixels) > 512:
            # اقتصار على أول 512 بكسل
            pixels = pixels[:512]
        
        # تحويل إلى مصفوفة numpy
        embedding = np.array(pixels, dtype='float32')
        
        # تطبيع القيم (0-255 إلى 0-1)
        embedding = embedding / 255.0
        
        return embedding
        
    except Exception as e:
        print(f"خطأ في حساب embedding الصورة: {e}")
        # إرجاع مصفوفة فارغة في حالة الخطأ
        return np.zeros(512, dtype='float32')
