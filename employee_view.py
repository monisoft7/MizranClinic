from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QLabel, QPushButton, QMessageBox, QHeaderView,
    QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

class EmployeeViewTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.current_page = 0
        self.page_size = 50
        self.setup_ui()
        self.load_departments()
        self.load_employees()

    def setup_ui(self):
        """تهيئة واجهة عرض الموظفين"""
        main_layout = QVBoxLayout()
    
        # مجموعة أدوات التحكم
        control_group = QGroupBox("أدوات التحكم")
        control_layout = QHBoxLayout()
    
        # فلترة حسب القسم
        self.department_combo = QComboBox()
        self.department_combo.addItem("جميع الأقسام")
        self.department_combo.currentTextChanged.connect(self.on_department_changed)
        control_layout.addWidget(QLabel("القسم:"))
        control_layout.addWidget(self.department_combo)

        # البحث بالاسم
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        control_layout.addWidget(QLabel("بحث:"))
        control_layout.addWidget(self.search_input)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # جدول الموظفين
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(10)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "الرقم الآلي", "الاسم", "الرقم الوطني", "القسم",
            "الدرجة", "تاريخ التعيين", "العلاوة", "رصيد الإجازات", "أيام العمل"
        ])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # أزرار التنقل بين الصفحات
        nav_group = QGroupBox("التنقل")
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("السابق")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("التالي")
        self.next_btn.clicked.connect(self.next_page)
        
        self.page_label = QLabel("الصفحة: 1")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        nav_group.setLayout(nav_layout)
        
        main_layout.addWidget(self.employees_table)
        main_layout.addWidget(nav_group)
        
        self.setLayout(main_layout)

    def refresh_departments(self, new_dept=None):
        """تحديث قائمة الأقسام مع إمكانية تحديد قسم جديد"""
        try:
            current = self.department_combo.currentText()
            self.department_combo.blockSignals(True)  # تعطيل الإشارات مؤقتاً
        
            self.department_combo.clear()
            self.department_combo.addItem("جميع الأقسام")
        
            self.db.execute_query("SELECT name FROM departments ORDER BY name")
            depts = [dept[0] for dept in self.db.cursor.fetchall()]
            self.department_combo.addItems(depts)
        
            if new_dept and new_dept in depts:
                self.department_combo.setCurrentText(new_dept)
            elif current in depts:
                self.department_combo.setCurrentText(current)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحديث الأقسام: {str(e)}")
        finally:
            self.department_combo.blockSignals(False)  # إعادة تفعيل الإشارات


    def on_department_changed(self, department):
        """تصفية الموظفين حسب القسم"""
        self.current_page = 0
        self.load_employees(filter_dept=department)
        self.page_label.setText(f"الصفحة: {self.current_page + 1}")

    def on_search_text_changed(self, text):
        """بحث الموظفين بالاسم"""
        self.current_page = 0
        self.load_employees(search_text=text)
        self.page_label.setText(f"الصفحة: {self.current_page + 1}")

    def load_departments(self):
        """تحميل قائمة الأقسام للفلترة"""
        try:
            self.db.execute_query("SELECT name FROM departments ORDER BY name")
            departments = [dept[0] for dept in self.db.cursor.fetchall()]
            current = self.department_combo.currentText()
            
            self.department_combo.clear()
            self.department_combo.addItem("جميع الأقسام")
            self.department_combo.addItems(departments)
            
            if current in departments:
                self.department_combo.setCurrentText(current)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"خطأ في تحميل الأقسام: {str(e)}"
            )

    def load_employees(self, filter_dept=None, search_text=None):
        """تحميل بيانات الموظفين مع إمكانية التصفية والبحث"""
        try:
            query = """
                SELECT id, serial_number, name, national_id, department,
                       job_grade, hiring_date, bonus, vacation_balance, work_days
                FROM employees
            """
            params = []
            
            conditions = []
            if filter_dept and filter_dept != "جميع الأقسام":
                conditions.append("department = ?")
                params.append(filter_dept)
                
            if search_text:
                conditions.append("name LIKE ?")
                params.append(f"%{search_text}%")
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY name LIMIT ? OFFSET ?"
            params.extend([self.page_size, self.current_page * self.page_size])
            
            self.db.execute_query(query, params, commit=False)
            employees = self.db.cursor.fetchall()
            
            self.employees_table.setRowCount(len(employees))
            for row_idx, employee in enumerate(employees):
                for col_idx, value in enumerate(employee):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.employees_table.setItem(row_idx, col_idx, item)
                
                # تلوين صفوف رصيد الإجازات المنخفض
                try:
                    balance = int(employee[8]) if employee[8] is not None else 0
                    if balance < 10:
                        for col in range(self.employees_table.columnCount()):
                            self.employees_table.item(row_idx, col).setBackground(QColor(255, 200, 200))
                except (ValueError, TypeError):
                    pass
            
            if not employees:
                empty_item = QTableWidgetItem("لا يوجد موظفين مسجلين")
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.employees_table.setRowCount(1)
                self.employees_table.setItem(0, 0, empty_item)
                self.employees_table.setSpan(0, 0, 1, self.employees_table.columnCount())
            
            # تحديث حالة أزرار التنقل
            self.update_navigation_buttons()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ في تحميل البيانات: {str(e)}"
            )

    def update_navigation_buttons(self):
        """تحديث حالة أزرار التنقل بين الصفحات"""
        self.prev_btn.setEnabled(self.current_page > 0)
        
        # التحقق مما إذا كانت هناك المزيد من الصفحات
        try:
            self.db.execute_query(
                "SELECT COUNT(*) FROM employees",
                commit=False
            )
            total_count = self.db.cursor.fetchone()[0]
            self.next_btn.setEnabled(total_count > (self.current_page + 1) * self.page_size)
        except Exception as e:
            print(f"Error checking next page: {e}")
            self.next_btn.setEnabled(False)

    def prev_page(self):
        """الانتقال إلى الصفحة السابقة"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_employees()
            self.page_label.setText(f"الصفحة: {self.current_page + 1}")

    def next_page(self):
        """الانتقال إلى الصفحة التالية"""
        self.current_page += 1
        self.load_employees()
        self.page_label.setText(f"الصفحة: {self.current_page + 1}")
