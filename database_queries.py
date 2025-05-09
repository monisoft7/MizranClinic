class DatabaseQueries:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_vacation_details(self, vacation_id):
        """جلب تفاصيل الإجازة"""
        self.db.execute_query("""
            SELECT v.id, v.type, v.start_date, v.end_date, v.duration, v.status,
                   e.id AS employee_id, e.name AS employee_name, e.telegram_user_id AS employee_telegram_id,
                   e.vacation_balance AS employee_balance
            FROM vacations v
            JOIN employees e ON v.employee_id = e.id
            WHERE v.id = ?
        """, (vacation_id,))
        row = self.db.cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "type": row[1],
            "start_date": row[2],
            "end_date": row[3],
            "duration": row[4],
            "status": row[5],
            "employee_id": row[6],
            "employee_name": row[7],
            "employee_telegram_id": row[8],
            "employee_balance": row[9]
        }

    def update_vacation_status(self, vacation_id, status, reason=None):
        """تحديث حالة الإجازة"""
        self.db.execute_query("""
            UPDATE vacations
            SET status = ?, rejection_reason = ?
            WHERE id = ?
        """, (status, reason, vacation_id), commit=True)

    def update_employee_balance(self, employee_id, amount):
        """تحديث رصيد الإجازات"""
        self.db.execute_query("""
            UPDATE employees
            SET vacation_balance = vacation_balance + ?
            WHERE id = ?
        """, (amount, employee_id), commit=True)

    def get_manager_id(self):
        """جلب معرف المدير"""
        self.db.execute_query("""
            SELECT telegram_user_id
            FROM employees
            WHERE job_grade = 'مدير'
            LIMIT 1
        """)
        row = self.db.cursor.fetchone()
        return row[0] if row else None