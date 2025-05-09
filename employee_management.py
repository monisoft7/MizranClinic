from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QPushButton, QComboBox, QDateEdit, QMessageBox, QCheckBox,
    QGroupBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QFormLayout, QHeaderView, QMenu, QTabWidget, QGridLayout
)
from dialogs import DepartmentDialog
from tabs.department_heads_tab import DepartmentHeadsTab

class EmployeeManagementTab(QWidget):
    def __init__(self, db_manager, main_window=None):
        super().__init__()
        self.db = db_manager
        self.main_window = main_window
        self.current_employee_id = None
        self.employees_table = QTableWidget()
        self.days_checkboxes = []
        self.day_periods = {}
        self.department_heads_btn = QPushButton("إدارة رؤساء الأقسام")

        # Special work status checkboxes
        self.secondment_checkbox = QCheckBox("الندب")
        self.dedication_checkbox = QCheckBox("تفرغ")

        self.init_ui_elements()
        self.setup_ui()
        self.load_departments()
        self.setup_connections()
        self.load_employees()

    def init_ui_elements(self):
        self.serial_input = QLineEdit()
        self.name_input = QLineEdit()
        self.national_id_input = QLineEdit()
        self.department_combo = QComboBox()
        self.job_grade_combo = QComboBox()
        self.hiring_date = QDateEdit(QDate.currentDate())
        self.grade_date = QDateEdit(QDate.currentDate())
        self.bonus_spinbox = QSpinBox()
        self.vacation_balance = QSpinBox()

        self.add_btn = QPushButton("إضافة جديد")
        self.save_btn = QPushButton("حفظ")
        self.edit_btn = QPushButton("تعديل")
        self.delete_btn = QPushButton("حذف")
        self.clear_btn = QPushButton("مسح")
        self.dept_btn = QPushButton("إدارة الأقسام")
        self.sort_id_btn = QPushButton("فرز بالأرقام")
        self.sort_name_btn = QPushButton("فرز بالأسماء")
        self.resize_btn = QPushButton("ضبط الأعمدة")
        self.refresh_btn = QPushButton("تحديث البيانات")

    def setup_ui(self):
        main_layout = QVBoxLayout()
        tabs = QTabWidget()

        basic_tab = QWidget()
        basic_layout = QFormLayout()
        basic_layout.addRow("الرقم الآلي:", self.serial_input)
        basic_layout.addRow("الاسم الكامل:", self.name_input)
        basic_layout.addRow("الرقم الوطني:", self.national_id_input)
        basic_layout.addRow("القسم:", self.department_combo)
        self.job_grade_combo.addItems([f"الدرجة {i}" for i in range(1, 15)])
        basic_layout.addRow("الدرجة الوظيفية:", self.job_grade_combo)
        basic_tab.setLayout(basic_layout)

        work_days_tab = QWidget()
        work_layout = QVBoxLayout()
        work_group = QGroupBox("أيام العمل والفترات")
        grid = QGridLayout()
        days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
        for row, day in enumerate(days):
            cb = QCheckBox(day)
            cb.setChecked(True)
            self.days_checkboxes.append(cb)
            period_combo = QComboBox()
            period_combo.addItems(["صباحية", "مسائية", "كامل اليوم"])
            self.day_periods[day] = period_combo
            grid.addWidget(cb, row, 0)
            grid.addWidget(period_combo, row, 1)
        # إضافة الندب والتفرغ مع أيام العمل
        work_group_layout = QVBoxLayout()
        work_group_layout.addLayout(grid)
        special_layout = QHBoxLayout()
        special_layout.addWidget(self.secondment_checkbox)
        special_layout.addWidget(self.dedication_checkbox)
        work_group_layout.addLayout(special_layout)
        work_group.setLayout(work_group_layout)
        work_layout.addWidget(work_group)
        work_days_tab.setLayout(work_layout)

        settings_tab = QWidget()
        settings_layout = QFormLayout()
        self.bonus_spinbox.setRange(0, 100)
        self.vacation_balance.setRange(0, 365)
        self.vacation_balance.setValue(30)
        settings_layout.addRow("تاريخ التعيين:", self.hiring_date)
        settings_layout.addRow("تاريخ الدرجة:", self.grade_date)
        settings_layout.addRow("العلاوة:", self.bonus_spinbox)
        settings_layout.addRow("رصيد الإجازات:", self.vacation_balance)
        settings_tab.setLayout(settings_layout)

        tabs.addTab(basic_tab, "البيانات الأساسية")
        tabs.addTab(work_days_tab, "أيام العمل")
        tabs.addTab(settings_tab, "الإعدادات")

        control_buttons = QHBoxLayout()
        control_buttons.addWidget(self.add_btn)
        control_buttons.addWidget(self.save_btn)
        control_buttons.addWidget(self.edit_btn)
        control_buttons.addWidget(self.delete_btn)
        control_buttons.addWidget(self.clear_btn)
        control_buttons.addWidget(self.dept_btn)
        control_buttons.addWidget(self.refresh_btn)

        sort_buttons = QHBoxLayout()
        sort_buttons.addWidget(self.sort_id_btn)
        sort_buttons.addWidget(self.sort_name_btn)
        sort_buttons.addWidget(self.resize_btn)

        self.employees_table.setColumnCount(10)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "الرقم الآلي", "الاسم", "الرقم الوطني", "القسم",
            "الدرجة", "تاريخ التعيين", "العلاوة", "رصيد الإجازات", "أيام العمل"
        ])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employees_table.cellClicked.connect(self.load_employee_for_edit)
        self.employees_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f0f0f0;
                gridline-color: #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        self.employees_table.setAlternatingRowColors(True)
        self.department_heads_btn.clicked.connect(self.open_department_heads)

        main_layout.addWidget(tabs)
        main_layout.addLayout(control_buttons)
        main_layout.addLayout(sort_buttons)
        main_layout.addWidget(QLabel("قائمة الموظفين:"))
        main_layout.addWidget(self.employees_table)
        main_layout.addWidget(self.department_heads_btn)
        self.setLayout(main_layout)

    def open_department_heads(self):
        """Open Department Heads Tab."""
        self.department_heads_tab = DepartmentHeadsTab(self.db)
        self.department_heads_tab.show()

    def setup_connections(self):
        self.add_btn.clicked.connect(self.prepare_add_employee)
        self.save_btn.clicked.connect(self.save_employee)
        self.edit_btn.clicked.connect(self.edit_employee)
        self.delete_btn.clicked.connect(self.delete_employee)
        self.clear_btn.clicked.connect(self.clear_form)
        self.dept_btn.clicked.connect(self.manage_departments)
        self.sort_id_btn.clicked.connect(lambda: self.sort_table(1))
        self.sort_name_btn.clicked.connect(lambda: self.sort_table(2))
        self.resize_btn.clicked.connect(self.resize_columns)
        self.refresh_btn.clicked.connect(self.load_employees)
        self.employees_table.cellClicked.connect(self.load_employee_for_edit)
        # ربط خيارات الندب والتفرغ
        self.secondment_checkbox.toggled.connect(self.toggle_special_work_status)
        self.dedication_checkbox.toggled.connect(self.toggle_special_work_status)

    def toggle_special_work_status(self):
        # تعطيل خيارات الأيام والفترات إذا تم اختيار الندب أو التفرغ
        any_checked = self.secondment_checkbox.isChecked() or self.dedication_checkbox.isChecked()
        for cb in self.days_checkboxes:
            cb.setEnabled(not any_checked)
        for period in self.day_periods.values():
            period.setEnabled(not any_checked)
        # إذا تم تحديد أحد الخيارين، ألغ تحديد الآخر
        sender = self.sender()
        if sender == self.secondment_checkbox and self.secondment_checkbox.isChecked():
            self.dedication_checkbox.setChecked(False)
        elif sender == self.dedication_checkbox and self.dedication_checkbox.isChecked():
            self.secondment_checkbox.setChecked(False)

    def load_employees(self):
        try:
            self.db.execute_query("""
                SELECT id, serial_number, name, national_id, department,
                       job_grade, hiring_date, bonus, vacation_balance, work_days
                FROM employees
                ORDER BY name
            """, commit=False)
            employees = self.db.cursor.fetchall()
            self.employees_table.setRowCount(len(employees))
            for row_idx, employee in enumerate(employees):
                for col_idx, value in enumerate(employee):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.employees_table.setItem(row_idx, col_idx, item)
            if not employees:
                empty_item = QTableWidgetItem("لا يوجد موظفين مسجلين")
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.employees_table.setRowCount(1)
                self.employees_table.setItem(0, 0, empty_item)
                self.employees_table.setSpan(0, 0, 1, self.employees_table.columnCount())
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل الموظفين:\n{str(e)}")

    def save_employee(self):
        errors = self.validate_input()
        if errors:
            QMessageBox.warning(self, "تحذير", "\n".join(errors))
            return
        try:
            employee_data = (
                self.serial_input.text().strip(),
                self.name_input.text().strip(),
                self.national_id_input.text().strip(),
                self.department_combo.currentText(),
                self.job_grade_combo.currentText(),
                self.hiring_date.date().toString("yyyy-MM-dd"),
                self.grade_date.date().toString("yyyy-MM-dd"),
                self.bonus_spinbox.value(),
                max(0, self.vacation_balance.value()),
                self.get_work_days()
            )
            if self.current_employee_id:
                query = """
                    UPDATE employees SET
                        serial_number=?, name=?, national_id=?, department=?,
                        job_grade=?, hiring_date=?, grade_date=?, bonus=?,
                        vacation_balance=?, work_days=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """
                self.db.execute_query(query, employee_data + (self.current_employee_id,))
            else:
                query = """
                    INSERT INTO employees (
                        serial_number, name, national_id, department,
                        job_grade, hiring_date, grade_date, bonus,
                        vacation_balance, work_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.db.execute_query(query, employee_data)
                self.db.execute_query("SELECT last_insert_rowid()")
                self.current_employee_id = self.db.cursor.fetchone()[0]
            QMessageBox.information(self, "تم", "تم حفظ بيانات الموظف بنجاح")
            self.load_employees()
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ:\n{str(e)}")

    def show_context_menu(self, pos):
        menu = QMenu()
        resize_action = menu.addAction("ضبط حجم الأعمدة")
        sort_name_action = menu.addAction("فرز بالأسماء")
        sort_id_action = menu.addAction("فرز بالأرقام")
        action = menu.exec(self.employees_table.viewport().mapToGlobal(pos))
        if action == resize_action:
            self.resize_columns()
        elif action == sort_name_action:
            self.sort_table(2)
        elif action == sort_id_action:
            self.sort_table(1)

    def prepare_add_employee(self):
        self.clear_form()
        self.current_employee_id = None
        self.serial_input.setFocus()
        QMessageBox.information(self, "معلومة", "الرجاء تعبئة بيانات الموظف الجديد ثم الضغط على حفظ")

    def sort_table(self, column):
        self.employees_table.sortByColumn(column, Qt.SortOrder.AscendingOrder)
        if column in [0, 1, 8]:
            for row in range(self.employees_table.rowCount()):
                item = self.employees_table.item(row, column)
                if item:
                    item.setData(Qt.ItemDataRole.DisplayRole, int(item.text()))

    def load_employee_for_edit(self, row, col):
        try:
            item = self.employees_table.item(row, 0)
            if item is not None:
                self.load_employee_data(item.text())
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل الموظف:\n{str(e)}")

    def load_employee_data(self, emp_id):
        try:
            self.db.execute_query(
                "SELECT id, serial_number, name, national_id, department, "
                "job_grade, hiring_date, grade_date, bonus, vacation_balance, work_days "
                "FROM employees WHERE id = ?",
                (emp_id,),
                commit=False
            )
            employee = self.db.cursor.fetchone()
            if not employee:
                QMessageBox.warning(self, "تحذير", "لم يتم العثور على بيانات الموظف")
                return
            self.current_employee_id = employee[0]
            self.serial_input.setText(employee[1])
            self.name_input.setText(employee[2])
            self.national_id_input.setText(employee[3])
            dept_index = self.department_combo.findText(employee[4])
            if dept_index >= 0:
                self.department_combo.setCurrentIndex(dept_index)
            self.job_grade_combo.setCurrentText(employee[5])
            self.hiring_date.setDate(QDate.fromString(employee[6], "yyyy-MM-dd"))
            self.grade_date.setDate(QDate.fromString(employee[7], "yyyy-MM-dd"))
            self.bonus_spinbox.setValue(employee[8])
            self.vacation_balance.setValue(employee[9] if employee[9] else 30)
            # معالجة خيار الندب والتفرغ
            if employee[10] == "الندب":
                self.secondment_checkbox.setChecked(True)
                self.dedication_checkbox.setChecked(False)
            elif employee[10] == "تفرغ":
                self.secondment_checkbox.setChecked(False)
                self.dedication_checkbox.setChecked(True)
            else:
                self.secondment_checkbox.setChecked(False)
                self.dedication_checkbox.setChecked(False)
                # تحميل الأيام والفترات
                work_days = employee[10].split(',') if employee[10] else []
                days_map = {"0":"السبت","1":"الأحد","2":"الإثنين",
                           "3":"الثلاثاء","4":"الأربعاء","5":"الخميس","6":"الجمعة"}
                for cb in self.days_checkboxes:
                    day_name = cb.text()
                    day_code = next((k for k,v in days_map.items() if v == day_name), None)
                    cb.setChecked(any(wd.startswith(f"{day_code}:") for wd in work_days))
                    if day_code:
                        for wd in work_days:
                            if wd.startswith(f"{day_code}:"):
                                period_code = wd.split(':')[1]
                                period_map = {"M":0, "E":1, "F":2}
                                self.day_periods[day_name].setCurrentIndex(period_map.get(period_code, 2))
                                break
            self.toggle_special_work_status()  # لضبط حالة التمكين/التعطيل
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل البيانات:\n{str(e)}")

    def validate_input(self):
        errors = []
        if not self.serial_input.text().strip():
            errors.append("حقل الرقم الآلي مطلوب")
        if not self.name_input.text().strip():
            errors.append("حقل الاسم الكامل مطلوب")
        national_id = self.national_id_input.text().strip()
        if not national_id:
            errors.append("حقل الرقم الوطني مطلوب")
        elif not national_id.isdigit() or len(national_id) != 12:
            errors.append("الرقم الوطني يجب أن يتكون من 12 رقمًا")
        if not self.current_employee_id:
            self.db.execute_query(
                "SELECT id FROM employees WHERE national_id=? OR serial_number=?",
                (national_id, self.serial_input.text().strip()),
                commit=False
            )
            if self.db.cursor.fetchone():
                errors.append("الرقم الوطني أو الآلي مسجل مسبقاً")
        try:
            vacation_balance = self.vacation_balance.value()
            if vacation_balance < 0:
                errors.append("رصيد الإجازات لا يمكن أن يكون سالباً")
        except Exception as e:
            errors.append("قيمة رصيد الإجازات غير صالحة")
        return errors

    def load_departments(self):
        try:
            self.db.execute_query("SELECT name FROM departments ORDER BY name")
            departments = [dept[0] for dept in self.db.cursor.fetchall()]
            self.department_combo.clear()
            self.department_combo.addItems(departments)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الأقسام: {str(e)}")

    def get_work_days(self):
        # إذا الندب أو التفرغ مفعل يرجع النص المناسب
        if self.secondment_checkbox.isChecked():
            return "الندب"
        if self.dedication_checkbox.isChecked():
            return "تفرغ"
        days_map = {
            "السبت": "0", "الأحد": "1", "الإثنين": "2",
            "الثلاثاء": "3", "الأربعاء": "4", 
            "الخميس": "5", "الجمعة": "6"
        }
        periods_map = {"صباحية": "M", "مسائية": "E", "كامل اليوم": "F"}
        work_days = []
        for cb in self.days_checkboxes:
            if cb.isChecked():
                day = cb.text()
                period = self.day_periods[day].currentText()
                work_days.append(f"{days_map[day]}:{periods_map[period]}")
        return ",".join(work_days)

    def resize_columns(self):
        header = self.employees_table.horizontalHeader()
        for col in range(self.employees_table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def edit_employee(self):
        if not self.current_employee_id:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد موظف أولاً")
            return
        self.save_employee()

    def delete_employee(self):
        if not self.current_employee_id:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد موظف أولاً")
            return
        confirm = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الموظف؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query(
                    "DELETE FROM employees WHERE id=?",
                    (self.current_employee_id,)
                )
                QMessageBox.information(self, "تم", "تم حذف الموظف بنجاح")
                self.clear_form()
                self.load_employees()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{str(e)}")

    def clear_form(self):
        self.current_employee_id = None
        self.serial_input.clear()
        self.name_input.clear()
        self.national_id_input.clear()
        self.department_combo.setCurrentIndex(0)
        self.job_grade_combo.setCurrentIndex(0)
        self.hiring_date.setDate(QDate.currentDate())
        self.grade_date.setDate(QDate.currentDate())
        self.bonus_spinbox.setValue(0)
        self.vacation_balance.setValue(30)
        self.secondment_checkbox.setChecked(False)
        self.dedication_checkbox.setChecked(False)
        for cb in self.days_checkboxes:
            cb.setChecked(True)
        for period in self.day_periods.values():
            period.setCurrentIndex(0)
        self.toggle_special_work_status()

    def manage_departments(self):
        dialog = DepartmentDialog(self)
        if dialog.exec():
            self.load_departments()
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'employee_view_tab'):
                self.main_window.employee_view_tab.refresh_departments()
            elif hasattr(self.parent(), 'employee_view_tab'):
                self.parent().employee_view_tab.refresh_departments()