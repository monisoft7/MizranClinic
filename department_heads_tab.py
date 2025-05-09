from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLineEdit, QMessageBox, QHeaderView, QInputDialog
)

class DepartmentHeadsTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

        self.heads_table = QTableWidget()
        self.employee_combo = QComboBox()
        self.department_combo = QComboBox()
        self.phone_input = QLineEdit()
        self.telegram_id_input = QLineEdit()
        self.add_head_btn = QPushButton("إضافة رئيس قسم")
        self.delete_head_btn = QPushButton("حذف رئيس قسم")
        self.approve_vacation_btn = QPushButton("موافقة على الإجازة")
        self.reject_vacation_btn = QPushButton("رفض الإجازة")

        self.setup_ui()
        self.load_employees()
        self.load_departments()
        self.load_heads()
        self.setup_connections()

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("الموظف:"))
        form_layout.addWidget(self.employee_combo)
        form_layout.addWidget(QLabel("القسم:"))
        form_layout.addWidget(self.department_combo)
        form_layout.addWidget(QLabel("رقم الهاتف:"))
        form_layout.addWidget(self.phone_input)
        form_layout.addWidget(QLabel("Telegram ID:"))
        form_layout.addWidget(self.telegram_id_input)
        form_layout.addWidget(self.add_head_btn)

        self.heads_table.setColumnCount(5)
        self.heads_table.setHorizontalHeaderLabels(["ID", "اسم الموظف", "القسم", "رقم الهاتف", "Telegram ID"])
        self.heads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.heads_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addLayout(form_layout)
        layout.addWidget(self.heads_table)
        layout.addWidget(self.delete_head_btn)

        # أزرار الإجازات (موافقة ورفض)
        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.approve_vacation_btn)
        actions_layout.addWidget(self.reject_vacation_btn)
        layout.addLayout(actions_layout)

        self.setLayout(layout)

    def load_employees(self):
        self.db.execute_query("SELECT id, name FROM employees ORDER BY name")
        employees = self.db.cursor.fetchall()
        self.employee_combo.clear()
        for emp_id, name in employees:
            self.employee_combo.addItem(name, emp_id)

    def load_departments(self):
        self.db.execute_query("SELECT name FROM departments ORDER BY name")
        departments = [row[0] for row in self.db.cursor.fetchall()]
        self.department_combo.clear()
        self.department_combo.addItems(departments)

    def load_heads(self):
        self.db.execute_query("""
            SELECT dh.id, e.name, dh.department, dh.phone_number, dh.telegram_user_id
            FROM department_heads dh
            JOIN employees e ON dh.employee_id = e.id
            ORDER BY e.name
        """)
        heads = self.db.cursor.fetchall()
        self.heads_table.setRowCount(len(heads))
        for row_idx, (head_id, emp_name, department, phone, telegram_id) in enumerate(heads):
            self.heads_table.setItem(row_idx, 0, QTableWidgetItem(str(head_id)))
            self.heads_table.setItem(row_idx, 1, QTableWidgetItem(emp_name))
            self.heads_table.setItem(row_idx, 2, QTableWidgetItem(department))
            self.heads_table.setItem(row_idx, 3, QTableWidgetItem(phone))
            self.heads_table.setItem(row_idx, 4, QTableWidgetItem(telegram_id or ""))

    def setup_connections(self):
        self.add_head_btn.clicked.connect(self.add_department_head)
        self.delete_head_btn.clicked.connect(self.delete_department_head)
        self.approve_vacation_btn.clicked.connect(self.approve_vacation)
        self.reject_vacation_btn.clicked.connect(self.reject_vacation)

    def add_department_head(self):
        emp_id = self.employee_combo.currentData()
        department = self.department_combo.currentText()
        phone = self.phone_input.text().strip()
        telegram_id = self.telegram_id_input.text().strip()

        if not department or not (phone or telegram_id):
            QMessageBox.warning(self, "تحذير", "يرجى إدخال القسم ورقم الهاتف أو Telegram ID.")
            return
        if telegram_id and not telegram_id.isdigit():
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال رقم تيليجرام الرقمي (chat_id) فقط وليس اسم مستخدم أو حروف.")
            return
        try:
            self.db.execute_query("""
                INSERT INTO department_heads (employee_id, department, phone_number, telegram_user_id)
                VALUES (?, ?, ?, ?)
            """, (emp_id, department, phone, telegram_id))
            QMessageBox.information(self, "نجاح", "تم إضافة رئيس القسم بنجاح.")
            self.load_heads()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإضافة:\n{str(e)}")

    def delete_department_head(self):
        selected_row = self.heads_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد رئيس قسم للحذف.")
            return
        head_id = int(self.heads_table.item(selected_row, 0).text())
        try:
            self.db.execute_query("DELETE FROM department_heads WHERE id = ?", (head_id,))
            QMessageBox.information(self, "نجاح", "تم حذف رئيس القسم بنجاح.")
            self.load_heads()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{str(e)}")

    def approve_vacation(self):
        """موافقة على الإجازة من رئيس القسم (تتحول للمدير)"""
        vacation_id, approved_by = self.select_pending_vacation()
        if vacation_id is None:
            return

        try:
            self.db.approve_vacation_by_head(vacation_id, approved=True, approved_by=approved_by)
            QMessageBox.information(self, "نجاح", "تم إرسال الطلب للمدير بانتظار الموافقة النهائية.")
            # هنا يمكنك استدعاء send_to_manager لإشعار المدير إذا كان لديك دالة لذلك
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الموافقة:\n{str(e)}")

    def reject_vacation(self):
        """رفض الإجازة من رئيس القسم"""
        vacation_id, approved_by = self.select_pending_vacation()
        if vacation_id is None:
            return

        # الحصول على سبب الرفض
        reason, ok = QInputDialog.getText(self, "سبب الرفض", "يرجى كتابة سبب الرفض:")
        if not ok:
            return

        try:
            self.db.approve_vacation_by_head(vacation_id, approved=False, notes=reason, approved_by=approved_by)
            QMessageBox.information(self, "تم الرفض", "تم رفض الإجازة وسيتم إشعار الموظف.")
            # هنا يمكنك استدعاء notify_employee_reject لإشعار الموظف إذا كان لديك دالة لذلك
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الرفض:\n{str(e)}")

    def select_pending_vacation(self):
        """
        نافذة اختيار الإجازة المعلقة لهذا القسم فقط
        تعيد (vacation_id, approved_by)
        """
        try:
            # استعلام لجلب الإجازات المعلقة لرئيس القسم حسب قسمه
            department = self.department_combo.currentText()
            self.db.execute_query("""
                SELECT v.id, e.name
                FROM vacations v
                JOIN employees e ON v.employee_id = e.id
                WHERE v.status = 'بانتظار موافقة رئيس القسم'
                  AND e.department = ?
                ORDER BY v.created_at ASC
            """, (department,))
            vacations = self.db.cursor.fetchall()
            if not vacations:
                QMessageBox.information(self, "لا يوجد طلبات", "لا توجد إجازات بانتظار موافقتك لهذا القسم حالياً.")
                return None, None

            # اختيار إجازة من القائمة
            items = [f"{row[1]} (ID: {row[0]})" for row in vacations]
            idx, ok = QInputDialog.getItem(self, "طلبات الإجازة", "اختر طلب الإجازة:", items, 0, False)
            if not ok:
                return None, None
            selected_vacation = vacations[items.index(idx)]
            return selected_vacation[0], selected_vacation[1]
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ أثناء جلب طلبات الإجازة: {str(e)}")
            return None, None
