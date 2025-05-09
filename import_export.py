from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QLabel,
    QGroupBox
)
from PyQt6.QtCore import Qt
import pandas as pd
from datetime import datetime

class ImportExportTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.import_btn = QPushButton("استيراد من Excel")
        self.export_btn = QPushButton("تصدير إلى Excel")  # تم تعريفه هنا
        self.template_btn = QPushButton("تحميل نموذج Excel")
        self.progress_bar = QProgressBar()
        self.status_label = QLabel()
        self.setup_ui()

    def refresh_employee_view(self):
        """تحديث نافذة عرض الموظفين"""
        try:
            # البحث عن نافذة عرض الموظفين في الهيكل التنظيمي
            parent = self.parent()
            while parent:
                if hasattr(parent, 'employee_view_tab'):
                    parent.employee_view_tab.load_employees()
                    break
                elif hasattr(parent, 'main_window') and hasattr(parent.main_window, 'employee_view_tab'):
                    parent.main_window.employee_view_tab.load_employees()
                    break
                parent = parent.parent()
        except Exception as e:
            print(f"حدث خطأ أثناء تحديث العرض: {str(e)}")

    def setup_ui(self):
        """تهيئة واجهة الاستيراد والتصدير"""
        main_layout = QVBoxLayout()
        
        # مجموعة الاستيراد
        import_group = QGroupBox("استيراد البيانات")
        import_layout = QVBoxLayout()
        
        self.import_btn.clicked.connect(self.import_data)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setVisible(False)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        import_layout.addWidget(self.import_btn)
        import_layout.addWidget(self.progress_bar)
        import_layout.addWidget(self.status_label)
        import_group.setLayout(import_layout)
        
        # مجموعة التصدير
        export_group = QGroupBox("تصدير البيانات")
        export_layout = QVBoxLayout()
        
        self.export_btn.clicked.connect(self.export_data)
        self.template_btn.clicked.connect(self.download_template)
        
        export_layout.addWidget(self.export_btn)
        export_layout.addWidget(self.template_btn)
        export_group.setLayout(export_layout)
        
        # تحسين مظهر الأزرار
        for btn in [self.import_btn, self.export_btn, self.template_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        
        # تحسين شريط التقدم
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        
        main_layout.addWidget(import_group)
        main_layout.addWidget(export_group)
        self.setLayout(main_layout)

    def import_data(self):
        """استيراد البيانات من ملف Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف Excel",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
    
        if not file_path:
            return
        
        confirm = QMessageBox.question(
            self,
            "تأكيد الاستيراد",
            "هل أنت متأكد من استيراد البيانات من هذا الملف؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.status_label.setText("جاري قراءة الملف...")
            self.progress_bar.setValue(10)
        
            # قراءة ملف Excel
            df = pd.read_excel(file_path)
        
            # التحقق من الأعمدة المطلوبة
            required_columns = ['serial_number', 'name', 'national_id']
            missing_columns = [col for col in required_columns if col not in df.columns]
        
            if missing_columns:
                raise ValueError(f"الأعمدة المفقودة: {', '.join(missing_columns)}")
        
            self.status_label.setText("جاري معالجة البيانات...")
            self.progress_bar.setValue(30)
        
            # تنظيف البيانات
            df = self.clean_import_data(df)
        
            self.status_label.setText("جاري حفظ البيانات...")
            self.progress_bar.setValue(50)
            
            # حفظ البيانات في قاعدة البيانات
            self.save_to_database(df)
        
            self.progress_bar.setValue(100)
            self.status_label.setText("تم الاستيراد بنجاح")
        
            QMessageBox.information(
                self,
                "تم",
                f"تم استيراد {len(df)} سجل بنجاح"
            )
            
            # تحديث عرض الموظفين إذا كان موجوداً
            if hasattr(self.parent(), 'employee_view_tab'):
                self.parent().employee_view_tab.load_employees()
            elif hasattr(self.parent(), 'main_window') and hasattr(self.parent().main_window, 'employee_view_tab'):
                self.parent().main_window.employee_view_tab.load_employees()
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء الاستيراد: {str(e)}"
            )
        finally:
            self.progress_bar.setVisible(False)

    def clean_import_data(self, df):
        """تنظيف وتهيئة البيانات المستوردة"""
        # تحويل الأعمدة الرقمية
        numeric_cols = ['bonus', 'vacation_balance']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
        # تحويل التواريخ
        date_cols = ['hiring_date', 'grade_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    
        # تعيين القيم الافتراضية
        if 'vacation_balance' in df.columns:
            df['vacation_balance'] = df['vacation_balance'].apply(lambda x: max(0, x))
        else:
            df['vacation_balance'] = 30  # القيمة الافتراضية
        
        if 'bonus' not in df.columns:
            df['bonus'] = 0
        
        if 'work_days' not in df.columns:
            df['work_days'] = "0:M,1:M,2:M,3:M,4:M,5:M,6:M"  # أيام العمل الافتراضية
        
        if 'department' not in df.columns:
            df['department'] = "غير محدد"
        
        return df

    def save_to_database(self, df):
        """حفظ البيانات المستوردة في قاعدة البيانات"""
        try:
            total = len(df)
            success = 0
            errors = []
        
            for idx, row in df.iterrows():
                try:
                    serial_number = str(row['serial_number']).strip()
                    if not serial_number:
                        continue
                        
                    self.db.execute_query(
                        "INSERT OR REPLACE INTO employees ("
                        "serial_number, name, national_id, department, "
                        "job_grade, hiring_date, grade_date, bonus, "
                        "vacation_balance, work_days"
                        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            serial_number,
                            str(row.get('name', '')).strip(),
                            str(row.get('national_id', '')).strip(),
                            str(row.get('department', 'غير محدد')).strip(),
                            str(row.get('job_grade', '')).strip(),
                            row.get('hiring_date', ''),
                            row.get('grade_date', ''),
                            int(row.get('bonus', 0)),
                            int(row.get('vacation_balance', 30)),
                            row.get('work_days', "0:M,1:M,2:M,3:M,4:M,5:M,6:M")
                        )
                    )
                    success += 1
                except Exception as e:
                    errors.append(f"سطر {idx+2}: {str(e)}")
                
                # تحديث شريط التقدم
                progress = 50 + int((idx + 1) / total * 50)
                self.progress_bar.setValue(progress)
                self.status_label.setText(f"جاري معالجة السجل {idx+1} من {total}")
            
            if errors:
                with open("import_errors.log", "w", encoding="utf-8") as f:
                    f.write("\n".join(errors))
                
                QMessageBox.warning(
                    self,
                    "تحذير",
                    f"تم استيراد {success} سجل بنجاح، مع {len(errors)} أخطاء.\n"
                    "تم حفظ تفاصيل الأخطاء في ملف import_errors.log"
                )
            if success > 0:  
                self.refresh_employee_view()
                
        except Exception as e:
            raise e

    def export_data(self):
        """تصدير البيانات إلى ملف Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ كملف Excel",
            f"employees_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
            
        try:
            # جلب البيانات من قاعدة البيانات
            self.db.execute_query("""
                SELECT 
                    serial_number, name, national_id, department,
                    job_grade, hiring_date, grade_date, bonus, vacation_balance
                FROM employees
                ORDER BY name
            """, commit=False)
            
            data = self.db.cursor.fetchall()
            
            if not data:
                QMessageBox.warning(
                    self,
                    "تحذير",
                    "لا توجد بيانات للتصدير"
                )
                return
                
            # إنشاء DataFrame
            columns = [
                'serial_number', 'name', 'national_id', 'department',
                'job_grade', 'hiring_date', 'grade_date', 'bonus', 'vacation_balance'
            ]
            df = pd.DataFrame(data, columns=columns)
            
            # تصدير إلى Excel
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(
                self,
                "تم",
                f"تم تصدير {len(data)} سجل بنجاح"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء التصدير: {str(e)}"
            )

    def download_template(self):
        """تحميل نموذج Excel للاستيراد"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ النموذج",
            "employee_template.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
            
        try:
            # إنشاء نموذج مع بيانات مثاليه
            sample_data = {
                'serial_number': ['1001', '1002'],
                'name': ['اسم الموظف 1', 'اسم الموظف 2'],
                'national_id': ['123456789012', '987654321098'],
                'department': ['الإدارة', 'التمريض'],
                'job_grade': ['الدرجة 1', 'الدرجة 2'],
                'hiring_date': ['2020-01-01', '2021-05-15'],
                'grade_date': ['2022-01-01', '2022-05-15'],
                'bonus': [10, 5],
                'vacation_balance': [30, 25],
                'work_days': ["0:M,1:M,2:M,3:M,4:M,5:M,6:M", "0:M,2:M,4:M"]
            }
            
            df = pd.DataFrame(sample_data)
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(
                self,
                "تم",
                "تم إنشاء النموذج بنجاح"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء إنشاء النموذج: {str(e)}"
            )