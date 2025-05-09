from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QLineEdit, QHeaderView, QGroupBox,
    QSpinBox, QInputDialog, QFileDialog
)
from PyQt6.QtCore import QDate, Qt
import pandas as pd

class AbsencesTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setup_ui()
        self.load_employees()
        self.load_absences()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # مجموعة حقول الإدخال
        input_group = QGroupBox("تسجيل غياب جديد")
        input_form = QFormLayout()
        
        self.employee_combo = QComboBox()
        input_form.addRow("الموظف:", self.employee_combo)
        
        self.absence_date = QDateEdit(QDate.currentDate())
        self.absence_date.setCalendarPopup(True)
        input_form.addRow("تاريخ الغياب:", self.absence_date)
        
        self.absence_type = QComboBox()
        self.absence_type.addItems(["غياب", "تأخير", "انصراف مبكر"])
        input_form.addRow("نوع الغياب:", self.absence_type)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(1)
        input_form.addRow("المدة (أيام):", self.duration_spin)
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات إضافية...")
        input_form.addRow("ملاحظات:", self.notes_input)
        
        self.save_btn = QPushButton("حفظ الغياب")
        self.save_btn.clicked.connect(self.save_absence)
        input_form.addRow(self.save_btn)

        export_btn = QPushButton("تقرير غياب شهر (Excel)")
        export_btn.clicked.connect(self.export_absences_month_dialog)
        main_layout.addWidget(export_btn)

        input_group.setLayout(input_form)
        main_layout.addWidget(input_group)

        # أدوات استخراج السجل لشهر معين
        filter_layout = QHBoxLayout()
        self.month_filter = QComboBox()
        self.month_filter.addItem("كل الشهور", "")
        # تعبئة أشهر السنة
        for y in range(QDate.currentDate().year(), QDate.currentDate().year()-5, -1):
            for m in range(1, 13):
                self.month_filter.addItem(f"{y}-{m:02d}", f"{y}-{m:02d}")
        self.month_filter.currentIndexChanged.connect(self.load_absences)
        filter_layout.addWidget(QLabel("عرض شهر:"))
        filter_layout.addWidget(self.month_filter)
        main_layout.addLayout(filter_layout)
        
        self.absences_table = QTableWidget()
        self.absences_table.setColumnCount(5)
        self.absences_table.setHorizontalHeaderLabels([
            "الموظف", "التاريخ", "النوع", "المدة", "ملاحظات"
        ])
        self.absences_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.absences_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        main_layout.addWidget(QLabel("سجل الغياب:"))
        main_layout.addWidget(self.absences_table)

        # زر لتصدير السجل لشهر
        self.export_btn = QPushButton("تصدير السجل (Excel)")
        self.export_btn.clicked.connect(self.export_month_absences)
        main_layout.addWidget(self.export_btn)
        
        self.setLayout(main_layout)


    def export_absences_month_dialog(self):
        year, ok1 = QInputDialog.getInt(self, "تقرير شهر", "أدخل السنة:", QDate.currentDate().year(), 2000, 2100)
        if not ok1:
            return
        month, ok2 = QInputDialog.getInt(self, "تقرير شهر", "أدخل رقم الشهر:", QDate.currentDate().month(), 1, 12)
        if not ok2:
            return
        all_names = ["الكل"] + [self.employee_combo.itemText(i) for i in range(self.employee_combo.count())]
        emp_name, ok3 = QInputDialog.getItem(self, "الموظف", "اختر الموظف (أو الكل):", all_names, 0, False)
        if not ok3:
            return
        emp_id = None
        if emp_name != "الكل":
            for i in range(self.employee_combo.count()):
                if self.employee_combo.itemText(i) == emp_name:
                    emp_id = self.employee_combo.itemData(i)
                    break
        self.export_absences_month(year, month, emp_id)

    def export_absences_month(self, year, month, emp_id=None):
        month_str = f"{year}-{month:02d}"
        if emp_id:
            query = """
                SELECT e.name, a.date, a.type, a.duration, a.notes
                FROM absences a JOIN employees e ON a.employee_id = e.id
                WHERE strftime('%Y-%m', a.date) = ? AND a.employee_id = ?
                ORDER BY a.date ASC
            """
            params = (month_str, emp_id)
        else:
            query = """
                SELECT e.name, a.date, a.type, a.duration, a.notes
                FROM absences a JOIN employees e ON a.employee_id = e.id
                WHERE strftime('%Y-%m', a.date) = ?
                ORDER BY a.date ASC
            """
            params = (month_str,)
        self.db.execute_query(query, params, commit=False)
        absences = self.db.cursor.fetchall()
        if not absences:
            QMessageBox.information(self, "لا يوجد بيانات", "لا يوجد غياب لهذا الشهر.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ تقرير الغياب", f"absences_{month_str}.xlsx", "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        df = pd.DataFrame(absences, columns=['الموظف', 'التاريخ', 'النوع', 'المدة', 'ملاحظات'])
        df.to_excel(file_path, index=False)
        QMessageBox.information(self, "تم", "تم حفظ التقرير بنجاح.")


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
            QMessageBox.critical(
                self,
                "خطأ",
                f"خطأ في تحميل الموظفين: {str(e)}"
            )

    def validate_absence(self):
        errors = []
        if not self.employee_combo.currentData():
            errors.append("الرجاء اختيار موظف")
        absence_date = self.absence_date.date()
        if absence_date > QDate.currentDate():
            errors.append("لا يمكن تسجيل غياب لتاريخ مستقبلي")
        return errors

    def save_absence(self):
        validation_errors = self.validate_absence()
        if validation_errors:
            QMessageBox.warning(
                self,
                "تحذير",
                "\n".join(validation_errors)
            )
            return
        try:
            emp_id = self.employee_combo.currentData()
            date = self.absence_date.date().toString("yyyy-MM-dd")
            abs_type = self.absence_type.currentText()
            duration = self.duration_spin.value()
            notes = self.notes_input.text()
            self.db.execute_query(
                "SELECT 1 FROM absences WHERE employee_id=? AND date=?",
                (emp_id, date),
                commit=False
            )
            if self.db.cursor.fetchone():
                QMessageBox.warning(
                    self,
                    "تحذير",
                    "تم تسجيل غياب لهذا الموظف في هذا التاريخ مسبقاً"
                )
                return
            self.db.execute_query(
                "INSERT INTO absences (employee_id, date, type, duration, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (emp_id, date, abs_type, duration, notes)
            )
            self.db.execute_query(
                "INSERT INTO audit_log (action, table_name, record_id, changes) "
                "VALUES (?, ?, ?, ?)",
                (
                    'INSERT',
                    'absences',
                    emp_id,
                    f"تم تسجيل {abs_type} للموظف في تاريخ {date}"
                )
            )
            QMessageBox.information(
                self,
                "تم",
                "تم تسجيل الغياب بنجاح"
            )
            self.load_absences()
            self.notes_input.clear()
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء الحفظ: {str(e)}"
            )

    def load_absences(self):
        """تحميل سجل الغياب وعرضه في الجدول حسب الشهر المحدد"""
        try:
            filter_month = self.month_filter.currentData()
            if filter_month:
                self.db.execute_query(
                    "SELECT e.name, a.date, a.type, a.duration, a.notes "
                    "FROM absences a JOIN employees e ON a.employee_id = e.id "
                    "WHERE strftime('%Y-%m', a.date) = ? "
                    "ORDER BY a.date DESC, e.name ASC",
                    (filter_month,),
                    commit=False
                )
            else:
                self.db.execute_query(
                    "SELECT e.name, a.date, a.type, a.duration, a.notes "
                    "FROM absences a JOIN employees e ON a.employee_id = e.id "
                    "ORDER BY a.date DESC, e.name ASC",
                    commit=False
                )
            absences = self.db.cursor.fetchall()
            self.absences_table.setRowCount(len(absences) if absences else 1)
            if not absences:
                empty_item = QTableWidgetItem("لا يوجد سجل غياب")
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.absences_table.setItem(0, 0, empty_item)
                self.absences_table.setSpan(0, 0, 1, self.absences_table.columnCount())
                return
            for row_idx, (name, date, abs_type, duration, notes) in enumerate(absences):
                self.absences_table.setItem(row_idx, 0, QTableWidgetItem(name))
                self.absences_table.setItem(row_idx, 1, QTableWidgetItem(date))
                self.absences_table.setItem(row_idx, 2, QTableWidgetItem(abs_type))
                self.absences_table.setItem(row_idx, 3, QTableWidgetItem(str(duration)))
                self.absences_table.setItem(row_idx, 4, QTableWidgetItem(notes))
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ في تحميل سجل الغياب: {str(e)}"
            )

    def export_month_absences(self):
        """تصدير سجل الغياب لشهر محدد إلى Excel"""
        import pandas as pd
        filter_month = self.month_filter.currentData()
        if not filter_month:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار شهر أولا")
            return
        try:
            self.db.execute_query(
                "SELECT e.name, a.date, a.type, a.duration, a.notes "
                "FROM absences a JOIN employees e ON a.employee_id = e.id "
                "WHERE strftime('%Y-%m', a.date) = ? "
                "ORDER BY a.date DESC, e.name ASC",
                (filter_month,),
                commit=False
            )
            absences = self.db.cursor.fetchall()
            if not absences:
                QMessageBox.information(self, "لا يوجد بيانات", "لا يوجد غياب لهذا الشهر")
                return
            file_path, _ = QFileDialog.getSaveFileName(
                self, "تصدير سجل الغياب", f"absences_{filter_month}.xlsx", "Excel Files (*.xlsx)"
            )
            if not file_path:
                return
            df = pd.DataFrame(absences, columns=["الموظف", "التاريخ", "النوع", "المدة", "ملاحظات"])
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "تم", "تم التصدير بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التصدير: {str(e)}")