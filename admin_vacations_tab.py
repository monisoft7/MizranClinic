from approval_flow import ApprovalFlow
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView
)
from PyQt6.QtCore import QTimer

class AdminVacationsTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.approval_flow = ApprovalFlow(db_manager)

        self.table = QTableWidget()
        self.refresh_btn = QPushButton("تحديث")
        self.approve_btn = QPushButton("موافقة")
        self.reject_btn = QPushButton("رفض")
        self.setup_ui()
        self.setup_connections()
        self.load_vacations()

        # Timer for checking new approved vacations
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_new_approved_vacations)
        self.timer.start(10000)  # كل 10 ثواني

    def setup_ui(self):
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.approve_btn)
        btn_layout.addWidget(self.reject_btn)

        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "اسم الموظف", "القسم", "نوع الإجازة", "من", "إلى", "المدة", "الحالة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("طلبات الإجازة بانتظار موافقة المدير:"))
        layout.addWidget(self.table)
        self.setLayout(layout)

    def setup_connections(self):
        self.refresh_btn.clicked.connect(self.load_vacations)
        self.approve_btn.clicked.connect(self.approve_vacation)
        self.reject_btn.clicked.connect(self.reject_vacation)

    def load_vacations(self):
        self.db.execute_query("""
            SELECT v.id, e.name, e.department, v.type, v.start_date, v.end_date, v.duration, v.status
            FROM vacations v
            JOIN employees e ON v.employee_id = e.id
            WHERE v.status = 'بانتظار موافقة المدير'
            ORDER BY v.created_at DESC
        """)
        vacations = self.db.cursor.fetchall()
        self.vacations_table.setRowCount(len(vacations))
        for row_idx, row in enumerate(vacations):
            for col_idx, value in enumerate(row):
                self.vacations_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def get_selected_vacation_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())


    def approve_vacation(self):
        vac_id = self.get_selected_vacation_id()
        if not vac_id:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد طلب إجازة للموافقة.")
            return

        self.db.execute_query("SELECT employee_id, type, duration, status FROM vacations WHERE id=?", (vac_id,))
        row = self.db.cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "خطأ", "تعذر العثور على الإجازة.")
            return
        emp_id, vac_type, duration, status = row

        if status != "بانتظار موافقة المدير":
            QMessageBox.warning(self, "خطأ", "لا يمكن الموافقة إلا على الطلبات بانتظار موافقة المدير.")
            return

        if vac_type == "سنوية":
            self.db.execute_query("SELECT vacation_balance FROM employees WHERE id=?", (emp_id,))
            balance = self.db.cursor.fetchone()[0]
            if duration > balance:
                QMessageBox.warning(self, "خطأ", "رصيد الإجازات غير كافٍ للموافقة على الطلب.")
                return
            self.db.execute_query(
                "UPDATE employees SET vacation_balance = vacation_balance - ? WHERE id=?",
                (duration, emp_id)
            )

        self.db.execute_query(
            "UPDATE vacations SET status='موافق' WHERE id=?",
            (vac_id,)
        )

        # إشعار الموظف بالموافقة
        self.notify_employee_status(emp_id, vac_id, approved=True)
        QMessageBox.information(self, "تمت الموافقة", "تمت الموافقة على الإجازة بنجاح.")
        self.load_vacations()


    def reject_vacation(self):
        vac_id = self.get_selected_vacation_id()
        if not vac_id:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد طلب إجازة للرفض.")
            return

        self.db.execute_query("SELECT employee_id, status FROM vacations WHERE id=?", (vac_id,))
        row = self.db.cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "خطأ", "تعذر العثور على الإجازة.")
            return
        emp_id, status = row

        if status != "بانتظار موافقة المدير":
            QMessageBox.warning(self, "خطأ", "لا يمكن رفض إلا الطلبات بانتظار موافقة المدير.")
            return

        self.db.execute_query(
            "UPDATE vacations SET status='مرفوض من المدير', seen_by_admin=0 WHERE id=?",
            (vac_id,)
        )

        self.notify_employee_status(emp_id, vac_id, approved=False)
        QMessageBox.information(self, "تم الرفض", "تم رفض الإجازة بنجاح.")
        self.load_vacations()


    def notify_employee_status(self, emp_id, vac_id, approved=True):
        """إشعار الموظف عبر التليجرام"""
        self.db.execute_query("SELECT telegram_user_id FROM employees WHERE id=?", (emp_id,))
        tg_row = self.db.cursor.fetchone()
        if tg_row and tg_row[0]:
            telegram_id = tg_row[0]
            try:
                from telegram import Bot
                bot = Bot("YOUR_BOT_TOKEN")  # استبدل بـ Token الخاص بك
                self.db.execute_query("SELECT type, start_date, end_date, duration FROM vacations WHERE id=?", (vac_id,))
                vac_row = self.db.cursor.fetchone()
                if approved:
                    msg = (
                        f"✅ تمت الموافقة على إجازتك ({vac_row[0]})\n"
                        f"من {vac_row[1]} إلى {vac_row[2]}\n"
                        f"المدة: {vac_row[3]} يوم\n"
                    )
                else:
                    msg = (
                        f"❌ تم رفض طلب الإجازة ({vac_row[0]}) من المدير.\n"
                        f"من {vac_row[1]} إلى {vac_row[2]}\n"
                        f"المدة: {vac_row[3]} يوم"
                    )
                bot.send_message(chat_id=int(telegram_id), text=msg)
            except Exception as e:
                print(f"تعذر إرسال إشعار التليجرام: {e}")


    def check_new_approved_vacations(self):
        """إشعار المدير بالإجازات الجديدة الموافَق عليها ولم يُطّلع عليها بعد"""
        self.db.execute_query("""
            SELECT id, employee_id, type, start_date, end_date
            FROM vacations
            WHERE status = 'موافق' AND (seen_by_admin IS NULL OR seen_by_admin = 0)
        """)
        new_approved = self.db.cursor.fetchall()
        for vac in new_approved:
            msg = (
                f"تمت الموافقة على طلب إجازة جديدة:\n"
                f"نوع الإجازة: {vac[2]}\n"
                f"من {vac[3]} إلى {vac[4]}"
            )
            QMessageBox.information(self, "إشعار إجازة جديدة", msg)
            self.db.execute_query("UPDATE vacations SET seen_by_admin = 1 WHERE id = ?", (vac[0],))