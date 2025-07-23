import json  # استيراد مكتبة التعامل مع JSON لقراءة وكتابة ملفات JSON
from datetime import datetime  # استيراد datetime للتعامل مع التواريخ والأوقات
import os  # استيراد مكتبة os للتعامل مع نظام الملفات

class SessionLogger:
    def __init__(self, log_file='session_logs.json'):  # دالة المُنشئ، تُحدد اسم ملف السجل الافتراضي
        self.log_file = log_file  # تخزين اسم ملف السجل في المتغير الخاص بالكائن
        self.ensure_log_file_exists()  # يستدعي الدالة ensure_log_file_exists() ليضمن أن الملف موجود (أو ينشئه إذا لم يكن موجودًا).

    def ensure_log_file_exists(self):
        if not os.path.exists(self.log_file):  # التحقق مما إذا كان ملف السجل غير موجود
            with open(self.log_file, 'w', encoding='utf-8') as f:  # إنشاء الملف وفتحه للكتابة مع ترميز UTF-8
                json.dump([], f)  # كتابة قائمة فارغة في الملف بصيغة JSON (مهيئ بداية السجل)

    # دالة تسجيل جلسة جديدة
    def log_session(self, username, session_start, session_duration, session_count):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:  # فتح ملف السجل للقراءة
                logs = json.load(f)  # تحميل محتوى الملف (قائمة السجلات) إلى متغير logs
        except:  # إذا حدث أي خطأ (مثلاً الملف غير موجود أو فارغ أو غير صالح)
            logs = []  # تعيين logs إلى قائمة فارغة لبدء التسجيل من جديد

        log_entry = {  # تكوين سجل جديد للجلسة على شكل قاموس يحتوي معلومات الجلسة
            'username': username,  # اسم المستخدم
            'session_start': session_start,  # بداية الجلسة (وقت البدء)
            'session_duration': session_duration,  # مدة الجلسة
            'session_count': session_count,  # عدد الجلسات التي قام بها المستخدم
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # وقت تسجيل السجل الحالي، منسق كسلسلة نصية
        }

        logs.append(log_entry)  # إضافة السجل الجديد إلى قائمة السجلات المحملة

        with open(self.log_file, 'w', encoding='utf-8') as f:  # فتح ملف السجل للكتابة مع ترميز UTF-8
            json.dump(logs, f, ensure_ascii=False, indent=4)  # كتابة قائمة السجلات (المحدثة) في الملف بصيغة JSON بشكل مقروء (منسق)

    def get_user_sessions(self, username):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:  # فتح ملف السجل للقراءة
                logs = json.load(f)  # تحميل محتويات الملف (قائمة السجلات)
            return [log for log in logs if log['username'] == username]  # إرجاع فقط السجلات التي تطابق اسم المستخدم المطلوب
        except:  # في حالة الخطأ (مثلاً الملف غير موجود)
            return []  # إرجاع قائمة فارغة (لا توجد سجلات)


# import json
# from datetime import datetime
# import os

# class SessionLogger:
#     def __init__(self, log_file='session_logs.json'):
#         self.log_file = log_file
#         self.ensure_log_file_exists()#يستدعي الدالة ensure_log_file_exists() ليضمن أن الملف موجود (أو ينشئه إذا لم يكن موجودًا).

#     def ensure_log_file_exists(self):
#         if not os.path.exists(self.log_file):
#             with open(self.log_file, 'w', encoding='utf-8') as f:
#                 json.dump([], f)
# #دالة تسجيل جلسة جديدة
#     def log_session(self, username, session_start, session_duration, session_count):
#         try:
#             with open(self.log_file, 'r', encoding='utf-8') as f:
#                 logs = json.load(f)
#         except:
#             logs = []

#         log_entry = {#تكوين سجل جديد للجلسة
#             'username': username,
#             'session_start': session_start,
#             'session_duration': session_duration,
#             'session_count': session_count,
#             'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         }

#         logs.append(log_entry)

#         with open(self.log_file, 'w', encoding='utf-8') as f:
#             json.dump(logs, f, ensure_ascii=False, indent=4)

#     def get_user_sessions(self, username):
#         try:
#             with open(self.log_file, 'r', encoding='utf-8') as f:
#                 logs = json.load(f)
#             return [log for log in logs if log['username'] == username]
#         except:
#             return [] 