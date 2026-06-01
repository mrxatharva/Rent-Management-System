# ================= IMPORTS =================
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from flask import Flask, request, jsonify
import threading

# ================= DATABASE =================
conn = sqlite3.connect("rent_management.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tenants(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    property_type TEXT,
    property_number TEXT,
    deposit REAL,
    deposit_mode TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS rent(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    month TEXT,
    amount REAL,
    transaction_id TEXT,
    payment_mode TEXT
)
""")

conn.commit()

# ================= FLASK API =================
app = Flask(__name__)

@app.route('/get_tenants')
def get_tenants():
    cursor.execute("SELECT id,name FROM tenants")
    return jsonify([{"id":i,"name":n} for i,n in cursor.fetchall()])


@app.route('/add_rent', methods=['POST'])
def api_add_rent():
    data = request.json
    cursor.execute("""
    INSERT INTO rent(tenant_id,month,amount,transaction_id,payment_mode)
    VALUES(?,?,?,?,?)
    """, (data['tenant_id'], data['month'],
          data['amount'], data['txn'], data['mode']))
    conn.commit()
    return jsonify({"status":"ok"})


def run_server():
    app.run(host='0.0.0.0', port=5000)

threading.Thread(target=run_server, daemon=True).start()

@app.route('/dashboard_summary', methods=['GET'])
def dashboard_summary():

    # Total tenants
    cursor.execute("SELECT COUNT(*) FROM tenants")
    total_tenants = cursor.fetchone()[0]

    # Total properties
    cursor.execute("SELECT COUNT(*) FROM tenants")
    total_properties = cursor.fetchone()[0]

    # Total collected rent
    cursor.execute("SELECT SUM(amount) FROM rent")
    collected = cursor.fetchone()[0]

    if collected is None:
        collected = 0

    # Pending calculation
    cursor.execute("SELECT COUNT(*) FROM tenants")
    total_tenants = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT tenant_id) FROM rent")
    paid_tenants = cursor.fetchone()[0]

    pending = (total_tenants - paid_tenants) * 10000

    return jsonify({
        "collected": collected,
        "pending": pending,
        "tenants": total_tenants,
        "properties": total_properties
    })

# ================= TKINTER =================
root = tk.Tk()
root.title("Rent Management System")
root.geometry("1200x700")
root.configure(bg="#eef2f7")

# ================= VARIABLES =================
name = tk.StringVar()
phone = tk.StringVar()
ptype = tk.StringVar()
pnum = tk.StringVar()
deposit = tk.StringVar()
dmode = tk.StringVar()

tenant = tk.StringVar()
month = tk.StringVar()
amount = tk.StringVar()
txn = tk.StringVar()
rmode = tk.StringVar()

selected_id = None

# ================= FUNCTIONS =================

def refresh_dropdown():
    cursor.execute("SELECT id,name FROM tenants")
    tenant_combo['values'] = [f"{i} - {n}" for i,n in cursor.fetchall()]

def clear():
    for v in [name,phone,ptype,pnum,deposit,dmode,tenant,month,amount,txn,rmode]:
        v.set("")

def add_tenant():
    cursor.execute("""
    INSERT INTO tenants(name,phone,property_type,property_number,deposit,deposit_mode)
    VALUES(?,?,?,?,?,?)
    """,(name.get(),phone.get(),ptype.get(),pnum.get(),deposit.get(),dmode.get()))
    conn.commit()
    show_records()
    refresh_dropdown()
    clear()

def modify():
    if not selected_id: return
    cursor.execute("""
    UPDATE tenants SET name=?,phone=?,property_type=?,property_number=?,deposit=?,deposit_mode=?
    WHERE id=?
    """,(name.get(),phone.get(),ptype.get(),pnum.get(),deposit.get(),dmode.get(),selected_id))
    conn.commit()
    show_records()

def delete():
    if not selected_id: return
    cursor.execute("DELETE FROM tenants WHERE id=?",(selected_id,))
    conn.commit()
    show_records()

def add_rent():
    if not tenant.get(): return
    tid = tenant.get().split(" - ")[0]
    cursor.execute("""
    INSERT INTO rent(tenant_id,month,amount,transaction_id,payment_mode)
    VALUES(?,?,?,?,?)
    """,(tid,month.get(),amount.get(),txn.get(),rmode.get()))
    conn.commit()
    messagebox.showinfo("Done","Rent Added")

def show_records():
    for i in tree.get_children():
        tree.delete(i)
    cursor.execute("SELECT * FROM tenants")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

def show_rent():
    for i in rent_tree.get_children():
        rent_tree.delete(i)
    if not tenant.get(): return
    tid = tenant.get().split(" - ")[0]
    cursor.execute("SELECT month,amount,transaction_id,payment_mode FROM rent WHERE tenant_id=?", (tid,))
    for row in cursor.fetchall():
        rent_tree.insert("", "end", values=row)

def select_row(e):
    global selected_id
    data = tree.item(tree.focus())['values']
    if data:
        selected_id = data[0]
        name.set(data[1])
        phone.set(data[2])
        ptype.set(data[3])
        pnum.set(data[4])
        deposit.set(data[5])
        dmode.set(data[6])

def exit_app():
    conn.close()
    root.destroy()

# ================= UI =================

# TITLE
tk.Label(root, text="RENT MANAGEMENT SYSTEM",
         font=("Arial",22,"bold"),
         bg="#1f3c88", fg="white").pack(fill="x")

# MAIN FRAME
frame = tk.Frame(root, bg="#eef2f7")
frame.pack(pady=15)

# LEFT FORM
labels = ["Name","Phone","Type","Number","Deposit","Mode"]
vars_ = [name,phone,ptype,pnum,deposit,dmode]

for i in range(6):
    tk.Label(frame,text=labels[i],bg="#eef2f7").grid(row=i,column=0,padx=10,pady=6,sticky="w")
    if labels[i]=="Type":
        ttk.Combobox(frame,textvariable=vars_[i],values=["Shop","Flat"],width=20).grid(row=i,column=1)
    elif labels[i]=="Mode":
        ttk.Combobox(frame,textvariable=vars_[i],
                     values=["Cash","UPI","Bank","Cheque"],width=20).grid(row=i,column=1)
    else:
        tk.Entry(frame,textvariable=vars_[i],width=22).grid(row=i,column=1)

# RIGHT RENT
tk.Label(frame,text="Tenant").grid(row=0,column=2,padx=40)
tenant_combo = ttk.Combobox(frame,textvariable=tenant,width=20)
tenant_combo.grid(row=0,column=3)

tk.Label(frame,text="Month").grid(row=1,column=2)
tk.Entry(frame,textvariable=month).grid(row=1,column=3)

tk.Label(frame,text="Amount").grid(row=2,column=2)
tk.Entry(frame,textvariable=amount).grid(row=2,column=3)

tk.Label(frame,text="Txn ID").grid(row=3,column=2)
tk.Entry(frame,textvariable=txn).grid(row=3,column=3)

tk.Label(frame,text="Mode").grid(row=4,column=2)
ttk.Combobox(frame,textvariable=rmode,
             values=["Cash","UPI","Bank","Cheque"]).grid(row=4,column=3)

# BUTTONS
btn = tk.Frame(root,bg="#eef2f7")
btn.pack(pady=10)

for t,c in [
    ("Add",add_tenant),
    ("Modify",modify),
    ("Delete",delete),
    ("Add Rent",add_rent),
    ("Show Rent",show_rent),
    ("Clear",clear),
    ("Exit",exit_app)
]:
    tk.Button(btn,text=t,width=12,bg="#2d3436",fg="white",command=c)\
        .pack(side="left",padx=6)

# TABLES
table_frame = tk.Frame(root)
table_frame.pack(fill="both",expand=True)

tree = ttk.Treeview(table_frame,
    columns=("ID","Name","Phone","Type","No","Deposit","Mode"),
    show="headings", height=8)

for col in ("ID","Name","Phone","Type","No","Deposit","Mode"):
    tree.heading(col,text=col)
    tree.column(col,width=130,anchor="center")

tree.pack(fill="x")
tree.bind("<ButtonRelease-1>",select_row)

rent_tree = ttk.Treeview(table_frame,
    columns=("Month","Amount","Txn","Mode"),
    show="headings", height=6)

for col in ("Month","Amount","Txn","Mode"):
    rent_tree.heading(col,text=col)
    rent_tree.column(col,width=150,anchor="center")

rent_tree.pack(fill="x",pady=10)

# INIT
refresh_dropdown()
show_records()

root.mainloop()