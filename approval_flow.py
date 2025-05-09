from notifications import send_telegram_notification
from database_queries import DatabaseQueries

class ApprovalFlow:
    def __init__(self, db_manager):
        self.db = DatabaseQueries(db_manager)

    def approve_by_head(self, vacation_id, head_id):
        """موافقة رئيس القسم على الإجازة"""
        vacation = self.db.get_vacation_details(vacation_id)
        if not vacation:
            return False, "تعذر العثور على طلب الإجازة."

        if vacation["status"] != "بانتظار موافقة رئيس القسم":
            return False, "لا يمكن الموافقة إلا على الطلبات بانتظار موافقة رئيس القسم."

        # تحديث حالة الإجازة
        self.db.update_vacation_status(vacation_id, "بانتظار موافقة المدير")

        # إرسال إشعار للمدير
        manager_id = self.db.get_manager_id()
        if manager_id:
            msg = (
                f"طلب إجازة جديد بانتظار موافقتك:\n"
                f"• الموظف: {vacation['employee_name']}\n"
                f"• النوع: {vacation['type']}\n"
                f"• من: {vacation['start_date']} إلى {vacation['end_date']}\n"
                f"• المدة: {vacation['duration']} يوم"
            )
            send_telegram_notification(manager_id, msg)

        return True, "تمت الموافقة من رئيس القسم وتم إرسال الطلب للمدير."

    def reject_by_head(self, vacation_id, head_id, reason):
        """رفض رئيس القسم لطلب الإجازة"""
        vacation = self.db.get_vacation_details(vacation_id)
        if not vacation:
            return False, "تعذر العثور على طلب الإجازة."

        if vacation["status"] != "بانتظار موافقة رئيس القسم":
            return False, "لا يمكن رفض إلا الطلبات بانتظار موافقة رئيس القسم."

        # تحديث حالة الإجازة
        self.db.update_vacation_status(vacation_id, "مرفوض من رئيس القسم", reason)

        # إرسال إشعار للموظف
        msg = (
            f"❌ تم رفض طلب الإجازة ({vacation['type']}) من رئيس القسم.\n"
            f"• السبب: {reason}\n"
            f"• من: {vacation['start_date']} إلى {vacation['end_date']}\n"
            f"• المدة: {vacation['duration']} يوم"
        )
        send_telegram_notification(vacation["employee_telegram_id"], msg)

        return True, "تم رفض الطلب وتم إشعار الموظف."

    def approve_by_manager(self, vacation_id, manager_id):
        """موافقة المدير على الإجازة"""
        vacation = self.db.get_vacation_details(vacation_id)
        if not vacation:
            return False, "تعذر العثور على طلب الإجازة."

        if vacation["status"] != "بانتظار موافقة المدير":
            return False, "لا يمكن الموافقة إلا على الطلبات بانتظار موافقة المدير."

        # خصم الرصيد إذا كانت الإجازة سنوية
        if vacation["type"] == "سنوية":
            if vacation["duration"] > vacation["employee_balance"]:
                return False, "رصيد الإجازات غير كافٍ للموافقة على الطلب."
            self.db.update_employee_balance(vacation["employee_id"], -vacation["duration"])

        # تحديث حالة الإجازة
        self.db.update_vacation_status(vacation_id, "موافق")

        # إرسال إشعار للموظف
        msg = (
            f"✅ تمت الموافقة النهائية على إجازتك ({vacation['type']}).\n"
            f"• من: {vacation['start_date']} إلى {vacation['end_date']}\n"
            f"• المدة: {vacation['duration']} يوم"
        )
        send_telegram_notification(vacation["employee_telegram_id"], msg)

        return True, "تمت الموافقة النهائية على الطلب."

    def reject_by_manager(self, vacation_id, manager_id, reason):
        """رفض المدير لطلب الإجازة"""
        vacation = self.db.get_vacation_details(vacation_id)
        if not vacation:
            return False, "تعذر العثور على طلب الإجازة."

        if vacation["status"] != "بانتظار موافقة المدير":
            return False, "لا يمكن رفض إلا الطلبات بانتظار موافقة المدير."

        # تحديث حالة الإجازة
        self.db.update_vacation_status(vacation_id, "مرفوض من المدير", reason)

        # إرسال إشعار للموظف
        msg = (
            f"❌ تم رفض طلب الإجازة ({vacation['type']}) من المدير.\n"
            f"• السبب: {reason}\n"
            f"• من: {vacation['start_date']} إلى {vacation['end_date']}\n"
            f"• المدة: {vacation['duration']} يوم"
        )
        send_telegram_notification(vacation["employee_telegram_id"], msg)

        return True, "تم رفض الطلب وتم إشعار الموظف."