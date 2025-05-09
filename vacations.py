from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QLineEdit, QHeaderView, QGroupBox,
    QSpinBox, QInputDialog
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor

class VacationsTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setup_ui()
        self.load_employees()
        self.load_vacations()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        input_group = QGroupBox("بيانات الإجازة")
        input_group.setStyleSheet("""
            QGroupBox {
                background-color: #f9f9f9;
                border: 1px solid #bdbdbd;
                border-radius: 8px;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                color: #2e7d32;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        input_form = QFormLayout()

        self.employee_combo = QComboBox()
        input_form.addRow("الموظف:", self.employee_combo)

        self.vacation_type = QComboBox()
        self.vacation_type.addItems([
            "سنوية", "وفاة", "حج",
            "زواج", "وضع", "مرضية"
        ])
        self.vacation_type.currentTextChanged.connect(self.handle_vacation_type_change)
        input_form.addRow("نوع الإجازة:", self.vacation_type)

        self.death_type_combo = QComboBox()
        self.death_type_combo.addItems(["وفاة من الدرجة الأولى", "وفاة من الدرجة الثانية"])
        self.death_type_combo.setVisible(False)
        self.death_type_combo.currentTextChanged.connect(self.update_death_vacation_duration)
        input_form.addRow("نوع الوفاة:", self.death_type_combo)

        # نوع الوضع (عادي/توأم)
        self.birth_type_combo = QComboBox()
        self.birth_type_combo.addItems(["وضع عادي", "وضع توأم"])
        self.birth_type_combo.setVisible(False)
        self.birth_type_combo.currentTextChanged.connect(self.update_birth_vacation_duration)
        input_form.addRow("نوع الوضع:", self.birth_type_combo)

        dates_group = QGroupBox("فترة الإجازة")
        dates_layout = QHBoxLayout()
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.update_duration)
        dates_layout.addWidget(QLabel("من:"))
        dates_layout.addWidget(self.start_date)
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.update_duration)
        dates_layout.addWidget(QLabel("إلى:"))
        dates_layout.addWidget(self.end_date)
        dates_group.setLayout(dates_layout)
        input_form.addRow(dates_group)

        self.days_count = QSpinBox()
        self.days_count.setRange(1, 365)
        self.days_count.setReadOnly(True)
        input_form.addRow("المدة (أيام):", self.days_count)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات إضافية...")
        input_form.addRow("ملاحظات:", self.notes_input)

        self.save_btn = QPushButton("حفظ الإجازة")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
        """)
        self.save_btn.clicked.connect(self.save_vacation)
        input_form.addRow(self.save_btn)

        input_group.setLayout(input_form)
        main_layout.addWidget(input_group)

        self.vacations_table = QTableWidget()
        self.vacations_table.setColumnCount(9)
        self.vacations_table.setHorizontalHeaderLabels([
            "ID", "الموظف", "النوع", "من", "إلى",
            "المدة", "الحالة", "الإجراء", "إلغاء"
        ])
        self.vacations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vacations_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.vacations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.vacations_table.setSortingEnabled(True)
        self.vacations_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                selection-background-color: #4CAF50;
            }
            QHeaderView::section {
                background-color: #607D8B;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
        """)
        self.vacations_table.verticalHeader().setDefaultSectionSize(38)

        main_layout.addWidget(QLabel("سجل الإجازات:"))
        main_layout.addWidget(self.vacations_table)
        self.setLayout(main_layout)
        self.update_duration()

    def handle_vacation_type_change(self, vac_type):
        self.death_type_combo.setVisible(vac_type == "وفاة")
        self.birth_type_combo.setVisible(vac_type == "وضع")
        today = QDate.currentDate()
        self.start_date.setDate(today)
        self.end_date.setDate(today)
        if vac_type == "حج":
            self.days_count.setValue(20)
        elif vac_type == "زواج":
            self.days_count.setValue(14)
        elif vac_type == "وضع":
            self.update_birth_vacation_duration()
        elif vac_type == "مرضية":
            self.days_count.setValue(1)
        elif vac_type == "سنوية":
            self.days_count.setValue(1)
        elif vac_type == "وفاة":
            self.update_death_vacation_duration()
        else:
            self.days_count.setValue(1)

    def update_death_vacation_duration(self):
        if self.death_type_combo.currentText() == "وفاة من الدرجة الأولى":
            self.days_count.setValue(7)
        else:
            self.days_count.setValue(3)

    def update_birth_vacation_duration(self):
        if self.birth_type_combo.currentText() == "وضع توأم":
            self.days_count.setValue(16 * 7)
        else:
            self.days_count.setValue(14 * 7)

    def load_employees(self):
        try:
            self.db.execute_query(
                "SELECT id, name FROM employees ORDER BY name"
            )
            employees = self.db.cursor.fetchall()
            self.employee_combo.clear()
            for emp_id, name in employees:
                self.employee_combo.addItem(name, emp_id)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الموظفين: {str(e)}")

    def update_duration(self):
        start = self.start_date.date()
        end = self.end_date.date()
        if start > end:
            self.end_date.setDate(start)
            end = start
        days = start.daysTo(end) + 1
        self.days_count.setValue(days)

    def validate_vacation_data(self):
        errors = []
        if not self.employee_combo.currentData():
            errors.append("الرجاء اختيار موظف")
        start_date = self.start_date.date()
        end_date = self.end_date.date()
        if start_date > end_date:
            errors.append("تاريخ النهاية يجب أن يكون بعد تاريخ البداية")
        if self.days_count.value() < 1:
            errors.append("المدة يجب أن تكون يوم واحد على الأقل")
        return errors

    def save_vacation(self):
        try:
            emp_id = self.employee_combo.currentData()
            if not emp_id:
                QMessageBox.warning(self, "تحذير", "الرجاء اختيار موظف")
                return
            vac_type = self.vacation_type.currentText()
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            duration = self.days_count.value()
            notes = self.notes_input.text() or "لا يوجد ملاحظات"
            relation = None

            if vac_type == "وفاة":
                death_type = self.death_type_combo.currentText()
                if death_type == "وفاة من الدرجة الأولى":
                    relations = ["أب", "أم", "ابن", "ابنة", "جد", "جدة", "زوج"]
                    relation, ok = QInputDialog.getItem(
                        self, "علاقة المتوفى",
                        "اختر صلة القرابة مع المتوفى:",
                        relations, 0, False
                    )
                    if not ok:
                        return
                    if relation == "زوج":
                        duration = 130
                else:
                    relation = "أقارب آخرون"
                self.update_death_vacation_duration()
                duration = self.days_count.value() if relation != "زوج" else 130

            birth_type = None
            if vac_type == "وضع":
                birth_type = self.birth_type_combo.currentText()
                # أضف نوع الوضع للملاحظة
                if birth_type == "وضع توأم":
                    notes = (notes + "\n" if notes else "") + "نوع الوضع: توأم"
                else:
                    notes = (notes + "\n" if notes else "") + "نوع الوضع: عادي"

            errors = self.validate_vacation_data()
            if errors:
                QMessageBox.warning(self, "تحذير", "\n".join(errors))
                return

            if self.check_vacation_conflict(emp_id, start_date, end_date):
                QMessageBox.warning(self, "تحذير", "هناك إجازة أخرى للموظف في هذه الفترة")
                return

            query = """
                INSERT INTO vacations (
                    employee_id, type, relation, start_date, end_date,
                    duration, notes, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """
            params = (
                emp_id, vac_type, relation, start_date, end_date,
                duration, notes, 'pending'
            )
            self.db.execute_query(query, params, commit=True)
            self.notify_manager(emp_id, vac_type, start_date, end_date)
            QMessageBox.information(
                self, "تم بنجاح",
                f"تم تقديم طلب الإجازة بنجاح\n"
                f"النوع: {vac_type}\n"
                f"المدة: {duration} يوم\n"
                f"من {start_date} إلى {end_date}\n"
                f"ملاحظات: {notes}"
            )
            self.load_vacations()
            self.notes_input.clear()
        except Exception as e:
            QMessageBox.critical(
                self, "خطأ في الحفظ",
                f"حدث خطأ أثناء حفظ الإجازة:\n{str(e)}\n"
                "الرجاء التأكد من صحة جميع البيانات والمحاولة مرة أخرى"
            )


    def refresh_data(self):
        """
        دالة زر تحديث البيانات، تعيد تحميل جدول الإجازات
        """
        self.load_vacations()

    def load_vacations(self):
        """
        تحميل جدول الإجازات بدون أزرار الموافقة/الرفض، بحيث يتم الاعتماد فقط من البوت.
        """
        try:
            self.vacations_table.setRowCount(0)
            query = """
                SELECT v.id, e.name, v.type, v.start_date,
                       v.end_date, v.duration, v.status, v.relation
                FROM vacations v
                JOIN employees e ON v.employee_id = e.id
                ORDER BY v.start_date DESC
            """
            self.db.execute_query(query)
            vacations = self.db.cursor.fetchall()
            if not vacations:
                self.vacations_table.setRowCount(1)
                for col in range(9):
                    self.vacations_table.setItem(0, col, QTableWidgetItem(''))
                self.vacations_table.setSpan(0, 0, 1, self.vacations_table.columnCount())
                self.vacations_table.setItem(0, 0, QTableWidgetItem("لا يوجد سجل إجازات"))
                return

            self.vacations_table.setRowCount(len(vacations))
            for row_idx, row in enumerate(vacations):
                vid, name, vtype, start, end, days, status, relation = row

                self.vacations_table.setItem(row_idx, 0, QTableWidgetItem(str(vid) if vid else ''))
                self.vacations_table.setItem(row_idx, 1, QTableWidgetItem(name if name else ''))
                if vtype == "وفاة" and relation:
                    display_type = f"وفاة ({relation})"
                else:
                    display_type = vtype if vtype else ''
                self.vacations_table.setItem(row_idx, 2, QTableWidgetItem(display_type))
                self.vacations_table.setItem(row_idx, 3, QTableWidgetItem(start if start else ''))
                self.vacations_table.setItem(row_idx, 4, QTableWidgetItem(end if end else ''))
                self.vacations_table.setItem(row_idx, 5, QTableWidgetItem(str(days) if days else ''))
                self.vacations_table.setItem(row_idx, 6, QTableWidgetItem(status if status else ''))

                # 7 - الإجراءات (لا تعرض أزرار موافقة/رفض أبداً)
                self.vacations_table.setCellWidget(row_idx, 7, QLabel("عن طريق البوت"))

                # 8 - زر الإلغاء أو مكانه
                if status == "موافق":
                    btn_cancel = QPushButton("إلغاء الإجازة")
                    self.style_button(btn_cancel, "#757575", "#616161", "#424242")
                    btn_cancel.clicked.connect(lambda _, vid=vid, vtype=vtype, days=days, status=status: self.cancel_vacation(vid, vtype, days, status))
                    cancel_widget = QWidget()
                    cancel_layout = QHBoxLayout()
                    cancel_layout.setContentsMargins(0, 0, 0, 0)
                    cancel_layout.addWidget(btn_cancel)
                    cancel_widget.setLayout(cancel_layout)
                    self.vacations_table.setCellWidget(row_idx, 8, cancel_widget)
                else:
                    self.vacations_table.setCellWidget(row_idx, 8, QLabel("-"))

                self.color_row_by_status(row_idx, status)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الإجازات: {str(e)}")


    def cancel_vacation(self, vacation_id, vac_type, days, status):
        try:
            if status != "موافق":
                QMessageBox.warning(self, "غير مسموح", "لا يمكن إلغاء إلا الإجازات الموافق عليها فقط.")
                return
            reply = QMessageBox.question(self, "تأكيد الإلغاء", "هل أنت متأكد من إلغاء هذه الإجازة؟ ستتم إعادة الأيام إلى الرصيد إذا كانت سنوية.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.db.execute_query("UPDATE vacations SET status='ملغاة' WHERE id=?", (vacation_id,), commit=True)
            if vac_type == "سنوية":
                self.db.execute_query("UPDATE employees SET vacation_balance = vacation_balance + ? WHERE id=(SELECT employee_id FROM vacations WHERE id=?)", (days, vacation_id), commit=True)
            QMessageBox.information(self, "تم", "تم إلغاء الإجازة بنجاح.")
            self.load_vacations()
            self.update_notification_count()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإلغاء: {str(e)}")

    def style_button(self, button, normal_color, hover_color, pressed_color):
        """
        تصميم مبسط وصغير للأزرار: ألوان واضحة، حجم صغير، حواف خفيفة، بدون ظل أو تكلف.
        """
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {normal_color};
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                padding: 2px 8px;
                min-width: 65px;
                min-height: 24px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)
        button.setMinimumWidth(65)
        button.setMinimumHeight(24)
        button.setGraphicsEffect(None)  # لا ظل

    def color_row_by_status(self, row_idx, status):
        color = QColor(255, 255, 255)
        if status == 'موافق':
            color = QColor(200, 255, 200)
        elif status == 'مرفوض':
            color = QColor(255, 200, 200)
        elif status == 'معلق':
            color = QColor(255, 255, 200)
        elif status == 'pending':
            color = QColor(255, 255, 255)
        for col in range(9):
            if self.vacations_table.item(row_idx, col):
                self.vacations_table.item(row_idx, col).setBackground(color)

    def update_status(self, vacation_id, status):
        """تحديث حالة الإجازة"""
        try:
            self.db.execute_query(
                "SELECT employee_id, type, duration, status FROM vacations WHERE id = ?",
                (vacation_id,), commit=False
            )
            emp_id, vac_type, duration, old_status = self.db.cursor.fetchone()

            # فقط عند الموافقة على السنوية، تحقق الرصيد وخصم
            if status == 'موافق' and vac_type == "سنوية":
                self.db.execute_query(
                    "SELECT vacation_balance FROM employees WHERE id=?", (emp_id,), commit=False
                )
                balance = self.db.cursor.fetchone()[0]
                if duration > balance:
                    QMessageBox.warning(self, "رصيد غير كافٍ", "لا يمكن الموافقة: رصيد الإجازات غير كافٍ لهذا الموظف!")
                    return

            self.db.execute_query(
                "UPDATE vacations SET status = ? WHERE id = ?", (status, vacation_id), commit=True
            )

            # خصم الرصيد عند الموافقة فقط
            if status == 'موافق' and vac_type == "سنوية":
                self.db.execute_query(
                    "UPDATE employees SET vacation_balance = vacation_balance - ? WHERE id = ?",
                    (duration, emp_id), commit=True
                )
            # في حالة إرجاع الحالة من موافق لأي حالة أخرى
            elif old_status == 'موافق' and status != 'موافق' and vac_type == "سنوية":
                self.db.execute_query(
                    "UPDATE employees SET vacation_balance = vacation_balance + ? WHERE id = ?",
                    (duration, emp_id), commit=True
                )

            self.load_vacations()
            self.update_notification_count()
            QMessageBox.information(self, "تم", f"تم تغيير الحالة إلى {status}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")

    def check_vacation_conflict(self, emp_id, start_date, end_date):
        try:
            self.db.execute_query("""
                SELECT COUNT(*) FROM vacations
                WHERE employee_id = ?
                AND status != 'مرفوض'
                AND (
                    (? BETWEEN start_date AND end_date)
                    OR (? BETWEEN start_date AND end_date)
                    OR (start_date BETWEEN ? AND ?)
                    OR (end_date BETWEEN ? AND ?)
                )
            """, (emp_id, start_date, end_date, start_date, end_date, start_date, end_date),
            commit=False)
            count = self.db.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"Error checking vacation conflict: {e}")
            return False

    def notify_manager(self, emp_id, vac_type, start, end):
        try:
            self.db.execute_query("""
                SELECT name FROM employees WHERE id = ?
            """, (emp_id,), commit=False)
            emp_name = self.db.cursor.fetchone()[0]
            print(f"إشعار: طلب إجازة جديد من {emp_name} ({vac_type} من {start} إلى {end})")
            self.update_notification_count()
        except Exception as e:
            print(f"Error sending notification: {e}")

    def update_notification_count(self):
        try:
            self.db.execute_query("""
                SELECT COUNT(*) FROM vacations
                WHERE status = 'pending'
            """, commit=False)
            count = self.db.cursor.fetchone()[0]
            if count > 0:
                self.notification_label.setText(f"لديك {count} طلبات إجازة بانتظار الموافقة")
            else:
                self.notification_label.clear()
        except Exception as e:
            print(f"Error updating notification count: {e}")