import sqlite3
conn = sqlite3.connect('employees.db')  # عدل الاسم إذا لزم
cur = conn.cursor()
cur.execute("ALTER TABLE department_heads ADD COLUMN department TEXT;")
conn.commit()
conn.close()
print("تم إضافة العمود department بنجاح!")