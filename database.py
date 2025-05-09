import sys
import sqlite3
import os
from PyQt6.QtCore import QDate  
from threading import Lock
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'employees.db')
        self.connection_lock = Lock()
        self.conn = None
        self.cursor = None
        self.initialize_connection()
        self.initialize_database()
        self.create_indexes()

    def initialize_connection(self):
        """تهيئة اتصال قاعدة البيانات"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"فشل في الاتصال بقاعدة البيانات: {e}")
            raise

    def initialize_database(self):
        """إنشاء الجداول إذا لم تكن موجودة"""
        tables = [
            """CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                national_id TEXT UNIQUE NOT NULL,
                department TEXT,
                job_grade TEXT,
                hiring_date TEXT,
                grade_date TEXT,
                bonus INTEGER DEFAULT 0,
                vacation_balance INTEGER DEFAULT 30,
                work_days TEXT,
                telegram_user_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS vacations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                subtype TEXT,
                relation TEXT, 
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                duration INTEGER NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'تحت الإجراء',
                approved_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS department_heads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                department TEXT NOT NULL,
                phone_number TEXT,
                telegram_user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )""",
            """CREATE TABLE IF NOT EXISTS absences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                duration INTEGER DEFAULT 1,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                UNIQUE(employee_id, date)
            )""",
            """CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                changes TEXT,
                user TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        ]

        try:
            for table in tables:
                self.cursor.execute(table)
            
            # إضافة الأقسام الافتراضية
            default_depts = [
                'الإدارة', 'التمريض', 
                'المحاسبة', 'المختبر', 
                'الصيدلة'
            ]
            
            insert_query = """
                INSERT OR IGNORE INTO departments 
                (name) VALUES (?)
            """
            
            for dept in default_depts:
                self.cursor.execute(insert_query, (dept,))
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"خطأ في إنشاء الجداول: {e}")
            self.conn.rollback()
            raise

    def create_indexes(self):
        """إنشاء الفهارس لتحسين الأداء"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_emp_national_id ON employees(national_id)",
            "CREATE INDEX IF NOT EXISTS idx_emp_department ON employees(department)",
            "CREATE INDEX IF NOT EXISTS idx_vacations_employee ON vacations(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_vacations_date ON vacations(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_absences_employee_date ON absences(employee_id, date)"
        ]
        
        try:
            for index in indexes:
                self.cursor.execute(index)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"خطأ في إنشاء الفهارس: {e}")

    def execute_query(self, query, params=(), commit=True):
        """تنفيذ استعلام مع معالجة الأخطاء"""
        with self.connection_lock:
            try:
                # تحويل التواريخ من QDate إلى نص
                processed_params = []
                for param in params:
                    if isinstance(param, QDate):
                        processed_params.append(param.toString("yyyy-MM-dd"))
                    else:
                        processed_params.append(param)
                
                result = self.cursor.execute(query, processed_params)
                if commit:
                    self.conn.commit()
                return result
            except sqlite3.Error as e:
                self.conn.rollback()
                raise Exception(f"خطأ في قاعدة البيانات: {str(e)}")


    def approve_vacation_by_head(self, vacation_id, approved, notes="", approved_by=None):
        """موافقة أو رفض رئيس القسم على الإجازة"""
        with self.connection_lock:
            try:
                # جلب بيانات الإجازة
                self.cursor.execute("SELECT status FROM vacations WHERE id=?", (vacation_id,))
                result = self.cursor.fetchone()
                if not result:
                    raise Exception("طلب الإجازة غير موجود")
                current_status = result[0]

                if current_status != "بانتظار موافقة رئيس القسم":
                    raise Exception("لا يمكن اعتماد هذا الطلب إلا من قبل رئيس القسم في مرحلته الصحيحة")

                if approved:
                    self.cursor.execute(
                        "UPDATE vacations SET status='بانتظار موافقة المدير', approved_by=? WHERE id=?",
                        (approved_by, vacation_id)
                    )
                else:
                    self.cursor.execute(
                        "UPDATE vacations SET status='مرفوض من رئيس القسم', notes=? WHERE id=?",
                        (notes, vacation_id)
                    )
                self.conn.commit()
                return True
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"خطأ في موافقة رئيس القسم: {e}")

    def approve_vacation_by_manager(self, vacation_id, approved, notes="", approved_by=None):
        """موافقة أو رفض المدير على الإجازة"""
        with self.connection_lock:
            try:
                self.cursor.execute("SELECT employee_id, type, duration, status FROM vacations WHERE id=?", (vacation_id,))
                vacation = self.cursor.fetchone()
                if not vacation:
                    raise Exception("طلب الإجازة غير موجود")
                employee_id, vac_type, duration, current_status = vacation

                if current_status != "بانتظار موافقة المدير":
                    raise Exception("لا يمكن اعتماد هذا الطلب إلا من قبل المدير في مرحلته الصحيحة")

                if approved:
                    # تحقق وخصم الرصيد إذا سنوية
                    if vac_type == "سنوية":
                        self.cursor.execute("SELECT vacation_balance FROM employees WHERE id=?", (employee_id,))
                        employee = self.cursor.fetchone()
                        if not employee:
                            raise Exception("الموظف غير موجود")
                        balance = employee[0]
                        if duration > balance:
                            raise Exception("رصيد الإجازات غير كافٍ")
                        self.cursor.execute(
                            "UPDATE employees SET vacation_balance = vacation_balance - ? WHERE id=?",
                            (duration, employee_id)
                        )
                    self.cursor.execute(
                        "UPDATE vacations SET status='موافق', approved_by=? WHERE id=?",
                        (approved_by, vacation_id)
                    )
                else:
                    self.cursor.execute(
                        "UPDATE vacations SET status='مرفوض من المدير', notes=? WHERE id=?",
                        (notes, vacation_id)
                    )
                self.conn.commit()
                return True
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"خطأ في موافقة المدير: {e}")


    def create_backup(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            backup_dir = os.path.join(
                os.path.dirname(__file__), 
                'backups'
            )
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            with open(backup_path, 'wb') as f:
                for line in self.conn.iterdump():
                    f.write(f"{line}\n".encode('utf-8'))
            return True
        except Exception as e:
            print(f"فشل في إنشاء النسخة الاحتياطية: {e}")
            return False

    def __del__(self):
        """إغلاق اتصال قاعدة البيانات"""
        if self.conn:
            try:
                if sys and sys.meta_path:
                    self.create_backup()
                self.conn.close()
            except Exception as e:
                print(f"تحذير: خطأ أثناء الإغلاق: {e}")