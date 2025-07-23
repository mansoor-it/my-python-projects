import logging  # استيراد مكتبة التسجيل (logging) المدمجة في بايثون

def setup_logger():
    # إعداد نظام التسجيل
    logger = logging.getLogger(__name__)  # الحصول على كائن الـ Logger الخاص بالوحدة الحالية
    logger.setLevel(logging.DEBUG)  # تعيين مستوى التسجيل إلى DEBUG لالتقاط جميع الرسائل من DEBUG فأعلى

    # إنشاء Handler لتسجيل السجلات في ملف
    file_handler = logging.FileHandler('app.log')  # إنشاء معالج يقوم بكتابة السجلات إلى ملف باسم app.log
    file_handler.setLevel(logging.INFO)  # تعيين مستوى التسجيل في هذا المعالج إلى INFO (تجاهل DEBUG)

    # إعداد Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # تنسيق السجل ليشمل الوقت واسم المسجل والمستوى والرسالة
    file_handler.setFormatter(formatter)  # تعيين المُنسّق للمعالج

    # إضافة Handler إلى Logger
    logger.addHandler(file_handler)  # ربط المعالج (الذي يسجل في ملف) بكائن الـ Logger

    return logger  # إرجاع كائن الـ Logger لاستخدامه في البرنامج
