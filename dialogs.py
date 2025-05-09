from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QFormLayout, QLabel, QMessageBox, QRadioButton,
    QDialogButtonBox, QDateEdit, QGroupBox
)
from PyQt6.QtCore import QDate

class DepartmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.load_departments()
        
    def setup_ui(self):
        """تهيئة واجهة إدارة الأقسام"""
        self.setWindowTitle("إدارة الأقسام")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # قسم إضافة قسم جديد
        add_group = QGroupBox("إضافة قسم جديد")
        add_layout = QFormLayout()
        
        self.new_department_input = QLineEdit()
        self.new_department_input.setPlaceholderText("أدخل اسم القسم")
        add_layout.addRow("اسم القسم:", self.new_department_input)
        
        self.add_btn = QPushButton("إضافة")
        self.add_btn.clicked.connect(self.add_department)
        add_layout.addRow(self.add_btn)
        
        add_group.setLayout(add_layout)
        
        # قسم حذف الأقسام
        delete_group = QGroupBox("حذف قسم")
        delete_layout = QFormLayout()
        
        self.department_combo = QComboBox()
        delete_layout.addRow("اختر قسم:", self.department_combo)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.clicked.connect(self.delete_department)
        delete_layout.addRow(self.delete_btn)
        
        delete_group.setLayout(delete_layout)
        
        # أزرار الإغلاق
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(add_group)
        layout.addWidget(delete_group)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def load_departments(self):
        """تحميل قائمة الأقسام"""
        try:
            self.parent.db.execute_query(
                "SELECT name FROM departments ORDER BY name"
            )
            departments = [dept[0] for dept in self.parent.db.cursor.fetchall()]
            self.department_combo.clear()
            self.department_combo.addItems(departments)
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"خطأ في تحميل الأقسام: {str(e)}"
            )

    def add_department(self):
        new_dept = self.new_department_input.text().strip()
        if not new_dept:
            QMessageBox.warning(self, "تحذير", "الرجاء إدخال اسم القسم")
            return
    
        try:
            self.parent.db.execute_query(
                "INSERT OR IGNORE INTO departments (name) VALUES (?)",
                (new_dept,)
            )
        
            QMessageBox.information(self, "تم", "تمت إضافة القسم بنجاح")
            self.new_department_input.clear()
    
            # تحديث قائمة الأقسام في هذه النافذة
            self.load_departments()
        
            # محاولة تحديث الأقسام في النوافذ الأخرى
            if hasattr(self.parent, 'load_departments'):
                self.parent.load_departments()
            
            if hasattr(self.parent, 'main_window') and hasattr(self.parent.main_window, 'employee_view_tab'):
                self.parent.main_window.employee_view_tab.refresh_departments(new_dept)
            elif hasattr(self.parent, 'employee_view_tab'):
                self.parent.employee_view_tab.refresh_departments(new_dept)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")

    def delete_department(self):
        """حذف قسم"""
        selected = self.department_combo.currentText()
        if not selected:
            return
            
        try:
            # التحقق من عدم وجود موظفين في القسم
            self.parent.db.execute_query(
                "SELECT COUNT(*) FROM employees WHERE department = ?",
                (selected,),
                commit=False
            )
            employee_count = self.parent.db.cursor.fetchone()[0]
            
            if employee_count > 0:
                QMessageBox.warning(
                    self,
                    "تحذير",
                    f"لا يمكن حذف القسم لأنه يحتوي على {employee_count} موظف"
                )
                return
                
            confirm = QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل أنت متأكد من حذف قسم '{selected}'؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.parent.db.execute_query(
                    "DELETE FROM departments WHERE name = ?",
                    (selected,)
                )
                
                QMessageBox.information(
                    self,
                    "تم",
                    "تم حذف القسم بنجاح"
                )
                self.load_departments()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء الحذف: {str(e)}"
            )

class SearchDialog(QDialog):
    """نافذة البحث المتقدم"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """تهيئة واجهة البحث"""
        self.setWindowTitle("البحث المتقدم")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # خيارات البحث
        options_group = QGroupBox("خيارات البحث")
        options_layout = QVBoxLayout()
        
        self.id_radio = QRadioButton("بحث بالرقم الوطني")
        self.name_radio = QRadioButton("بحث بالاسم")
        self.date_radio = QRadioButton("بحث بالتاريخ")
        
        self.id_radio.setChecked(True)
        
        options_layout.addWidget(self.id_radio)
        options_layout.addWidget(self.name_radio)
        options_layout.addWidget(self.date_radio)
        options_group.setLayout(options_layout)
        
        # حقول البحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("أدخل كلمة البحث...")
        
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_from.setVisible(False)
        
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setVisible(False)
        
        # ربط تغيير خيارات البحث
        self.id_radio.toggled.connect(lambda: self.update_search_fields('id'))
        self.name_radio.toggled.connect(lambda: self.update_search_fields('name'))
        self.date_radio.toggled.connect(lambda: self.update_search_fields('date'))
        
        # أزرار التنفيذ
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(options_group)
        layout.addWidget(QLabel("كلمة البحث:"))
        layout.addWidget(self.search_input)
        layout.addWidget(QLabel("من تاريخ:"))
        layout.addWidget(self.date_from)
        layout.addWidget(QLabel("إلى تاريخ:"))
        layout.addWidget(self.date_to)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def update_search_fields(self, search_type):
        """تحديث حقول البحث حسب النوع المحدد"""
        if search_type == 'date':
            self.search_input.setVisible(False)
            self.date_from.setVisible(True)
            self.date_to.setVisible(True)
        else:
            self.search_input.setVisible(True)
            self.date_from.setVisible(False)
            self.date_to.setVisible(False)
            self.search_input.setFocus()

    def get_search_params(self):
        """الحصول على معايير البحث"""
        if self.id_radio.isChecked():
            return {
                'type': 'national_id',
                'value': self.search_input.text().strip()
            }
        elif self.name_radio.isChecked():
            return {
                'type': 'name',
                'value': self.search_input.text().strip()
            }
        else:
            return {
                'type': 'date',
                'from': self.date_from.date().toString("yyyy-MM-dd"),
                'to': self.date_to.date().toString("yyyy-MM-dd")
            }