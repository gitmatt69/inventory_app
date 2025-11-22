from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date
import os
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.db')

app = Flask(__name__)
app.secret_key = 'GitHubActionsSecretKey'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/suppliers')
def suppliers():
    conn = get_db_connection()
    suppliers = conn.execute('SELECT * FROM Suppliers').fetchall()
    conn.close()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/inventory', methods=['GET'])
def inventory():
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    stock_filter = request.args.get('stock', '').strip()

    conn = get_db_connection()

    query = '''
        SELECT Items.item_id, Items.item_name, Items.description,
               Categories.category_name, Suppliers.supplier_name,
               Items.unit_price, Items.reorder_level,
               IFNULL(SUM(Stock.quantity), 0) AS total_stock
        FROM Items
        LEFT JOIN Categories ON Items.category_id = Categories.category_id
        LEFT JOIN Suppliers ON Items.supplier_id = Suppliers.supplier_id
        LEFT JOIN Stock ON Items.item_id = Stock.item_id
    '''
    conditions = []
    params = []

    if search_query:
        conditions.append("(Items.item_name LIKE ? OR Items.description LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if category_filter:
        conditions.append("Categories.category_name = ?")
        params.append(category_filter)

    query += " WHERE " + " AND ".join(conditions) if conditions else ""
    query += '''
        GROUP BY Items.item_id
        ORDER BY Items.item_id
    '''
    items = conn.execute(query, params).fetchall()

    if stock_filter:
        filtered_items = []
        for item in items:
            total_stock = item['total_stock']
            reorder_level = item['reorder_level']
            if stock_filter == 'in-stock' and total_stock > reorder_level:
                filtered_items.append(item)
            elif stock_filter == 'low-stock' and 0 < total_stock <= reorder_level:
                filtered_items.append(item)
            elif stock_filter == 'out-of-stock' and total_stock == 0:
                filtered_items.append(item)
        items = filtered_items

    conn.close()
    return render_template('inventory.html', items=items)



@app.route('/orders')
def orders():
    conn = get_db_connection()
    orders_list = conn.execute('''
        SELECT 
            po.po_id, 
            s.supplier_name, 
            po.order_date, 
            po.status, 
            po.expected_delivery_date,
            i.item_name,
            pod.quantity_ordered
        FROM PurchaseOrders po
        JOIN Suppliers s ON po.supplier_id = s.supplier_id
        JOIN PurchaseOrderDetails pod ON po.po_id = pod.po_id
        JOIN Items i ON pod.item_id = i.item_id
        ORDER BY po.po_id
    ''').fetchall()
    conn.close()
    return render_template('orders.html', orders=orders_list)

@app.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    conn = get_db_connection()

    if request.method == 'POST':
        supplier_id = int(request.form['supplier_id'])
        item_id = int(request.form['item_id'])
        quantity_ordered = int(request.form['quantity'])
        unit_cost = float(request.form['unit_cost'])
        expected_delivery_date = request.form['order_date']

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO PurchaseOrders (supplier_id, order_date, status, expected_delivery_date)
            VALUES (?, DATE('now'), 'Pending', ?)
        """, (supplier_id, expected_delivery_date))

        po_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO PurchaseOrderDetails (po_id, item_id, quantity_ordered)
            VALUES (?, ?, ?)
        """, (po_id, item_id, quantity_ordered))

        conn.commit()
        conn.close()

        flash("Purchase order created!", "success")
        return redirect(url_for("orders"))

    suppliers = conn.execute("SELECT * FROM Suppliers").fetchall()
    items = conn.execute("SELECT * FROM Items").fetchall()
    conn.close()

    return render_template("add_order.html", suppliers=suppliers, items=items)

@app.route('/orders/edit/<int:po_id>', methods=['GET', 'POST'])
def edit_order(po_id):
    conn = get_db_connection()
    
    
    order = conn.execute(
        "SELECT * FROM PurchaseOrders WHERE po_id = ?", (po_id,)
    ).fetchone()
    
    
    order_details = conn.execute(
        "SELECT * FROM PurchaseOrderDetails WHERE po_id = ?", (po_id,)
    ).fetchall()
    
    if request.method == 'POST':
        supplier_id = int(request.form['supplier_id'])
        order_date = request.form['order_date']
        expected_delivery_date = request.form['expected_delivery_date']
        status = request.form['status']

       
        conn.execute("""
            UPDATE PurchaseOrders
            SET supplier_id = ?, order_date = ?, expected_delivery_date = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE po_id = ?
        """, (supplier_id, order_date, expected_delivery_date, status, po_id))

        
        for detail in order_details:
            quantity = int(request.form.get(f'quantity_{detail["po_detail_id"]}'))
            unit_cost = float(request.form.get(f'unit_cost_{detail["po_detail_id"]}'))
            conn.execute("""
                UPDATE PurchaseOrderDetails
                SET quantity_ordered = ?, unit_cost = ?, updated_at = CURRENT_TIMESTAMP
                WHERE po_detail_id = ?
            """, (quantity, unit_cost, detail["po_detail_id"]))

        conn.commit()
        conn.close()

        flash("Purchase order updated!", "success")
        return redirect(url_for("orders"))

    suppliers = conn.execute("SELECT * FROM Suppliers").fetchall()
    items = conn.execute("SELECT * FROM Items").fetchall()
    conn.close()

    return render_template("edit_order.html", order=order, order_details=order_details, suppliers=suppliers, items=items)

@app.route('/orders/delete/<int:po_id>')
def delete_order(po_id):
    conn = get_db_connection()
    
    # Delete line items first (foreign key dependency)
    conn.execute("DELETE FROM PurchaseOrderDetails WHERE po_id = ?", (po_id,))
    
    # Delete order header
    conn.execute("DELETE FROM PurchaseOrders WHERE po_id = ?", (po_id,))
    
    conn.commit()
    conn.close()
    
    flash("Purchase order deleted successfully!", "success")
    return redirect(url_for('orders'))

@app.route('/reports')
def reports():
    conn = get_db_connection()
    report_data = conn.execute('''
        SELECT c.category_name, SUM(IFNULL(s.quantity,0)) AS total_stock
        FROM Categories c
        LEFT JOIN Items i ON c.category_id = i.category_id
        LEFT JOIN Stock s ON i.item_id = s.item_id
        GROUP BY c.category_id
    ''').fetchall()
    conn.close()
    return render_template('reports.html', report_data=report_data)

@app.route('/sales_orders')
def sales_orders():
    conn = get_db_connection()
    sales_summary = conn.execute('''
        SELECT 
            so.so_id,
            c.customer_name,
            so.order_date,
            so.status,
            SUM(sod.quantity_sold) AS total_items,
            SUM(sod.quantity_sold * sod.unit_price) AS total_value
        FROM SalesOrders so
        JOIN Customers c ON so.customer_id = c.customer_id
        JOIN SalesOrderDetails sod ON so.so_id = sod.so_id
        GROUP BY so.so_id
        ORDER BY so.so_id DESC
    ''').fetchall()
    conn.close()
    return render_template('sales_orders.html', sales_summary=sales_summary)

@app.route('/performance')
def performance():
    conn = get_db_connection()
    performance_data = conn.execute('''
        SELECT i.item_name, SUM(IFNULL(s.quantity,0)) AS total_stock, i.reorder_level
        FROM Items i
        LEFT JOIN Stock s ON i.item_id = s.item_id
        GROUP BY i.item_id
        HAVING total_stock < i.reorder_level
    ''').fetchall()
    
    sales_summary = conn.execute('''
        SELECT 
            so.so_id,
            c.customer_name,
            so.order_date,
            so.status,
            SUM(sod.quantity_sold) AS total_items,
            SUM(sod.quantity_sold * sod.unit_price) AS total_value
        FROM SalesOrders so
        JOIN Customers c ON so.customer_id = c.customer_id
        JOIN SalesOrderDetails sod ON so.so_id = sod.so_id
        GROUP BY so.so_id
        ORDER BY so.so_id DESC
    ''').fetchall()
    conn.close()
    return render_template('performance.html', performance_data=performance_data, sales_summary=sales_summary)

@app.route('/sales_orders/add', methods=['GET', 'POST'])
def add_sales_order():
    conn = get_db_connection()
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        item_id = request.form['item_id']
        quantity_sold = request.form['quantity_sold']
        unit_price = request.form['unit_price']
        shipping_address = request.form['shipping_address']

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SalesOrders (customer_id, order_date, status, shipping_address)
            VALUES (?, DATE('now'), 'Pending', ?)
        """, (customer_id, shipping_address))
        so_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO SalesOrderDetails (so_id, item_id, quantity_sold, unit_price)
            VALUES (?, ?, ?, ?)
        """, (so_id, item_id, quantity_sold, unit_price))

        conn.commit()
        conn.close()
        flash("Sales order created!", "success")
        return redirect(url_for('sales_orders'))

    customers = conn.execute("SELECT * FROM Customers").fetchall()
    items = conn.execute("SELECT * FROM Items").fetchall()
    current_date = date.today().isoformat()
    conn.close()
    return render_template('add_sales_order.html', customers=customers, items=items, current_date=current_date)

@app.route('/sales_orders/edit/<int:so_id>', methods=['GET', 'POST'])
def edit_sales_order(so_id):
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM SalesOrders WHERE so_id = ?", (so_id,)).fetchone()
    order_details = conn.execute("SELECT * FROM SalesOrderDetails WHERE so_id = ?", (so_id,)).fetchall()

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        status = request.form['status']
        shipping_address = request.form['shipping_address']
        order_date = request.form['order_date']

        conn.execute("""
            UPDATE SalesOrders
            SET customer_id=?, status=?, shipping_address=?, order_date=?, updated_at=CURRENT_TIMESTAMP
            WHERE so_id=?
        """, (customer_id, status, shipping_address, order_date, so_id))

        for detail in order_details:
            quantity = request.form.get(f'quantity_{detail["so_detail_id"]}')
            unit_price = request.form.get(f'unit_price_{detail["so_detail_id"]}')
            conn.execute("""
                UPDATE SalesOrderDetails
                SET quantity_sold=?, unit_price=?, updated_at=CURRENT_TIMESTAMP
                WHERE so_detail_id=?
            """, (quantity, unit_price, detail['so_detail_id']))

        conn.commit()
        conn.close()
        flash("Sales order updated!", "success")
        return redirect(url_for('sales_orders'))

    customers = conn.execute("SELECT * FROM Customers").fetchall()
    items = conn.execute("SELECT * FROM Items").fetchall()
    conn.close()
    return render_template('edit_sales_order.html', order=order, order_details=order_details, customers=customers, items=items)

@app.route('/sales_orders/delete/<int:so_id>')
def delete_sales_order(so_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM SalesOrderDetails WHERE so_id = ?", (so_id,))
    conn.execute("DELETE FROM SalesOrders WHERE so_id = ?", (so_id,))
    conn.commit()
    conn.close()
    flash("Sales order deleted successfully!", "success")
    return redirect(url_for('sales_orders'))

@app.route('/settings')
def settings():
    conn = get_db_connection()
    users = conn.execute('SELECT user_id, username, role, email FROM Users').fetchall()
    conn.close()
    return render_template('settings.html', users=users)


@app.route('/inventory/add', methods=['GET', 'POST'])
def add_item():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category_id']
        supplier_id = request.form['supplier_id']
        unit_price = request.form['unit_price']
        reorder_level = request.form['reorder_level']

        conn.execute('''
            INSERT INTO Items (item_name, description, category_id, supplier_id, unit_price, reorder_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, category_id, supplier_id, unit_price, reorder_level))
        conn.commit()
        conn.close()
        flash('Item added successfully!', 'success')
        return redirect(url_for('inventory'))

    categories = conn.execute('SELECT * FROM Categories').fetchall()
    suppliers = conn.execute('SELECT * FROM Suppliers').fetchall()
    conn.close()
    return render_template('add_inventory.html', categories=categories, suppliers=suppliers)

@app.route('/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM Items WHERE item_id = ?', (item_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category_id']
        supplier_id = request.form['supplier_id']
        unit_price = request.form['unit_price']
        reorder_level = request.form['reorder_level']

        conn.execute('''
            UPDATE Items
            SET item_name=?, description=?, category_id=?, supplier_id=?, unit_price=?, reorder_level=?
            WHERE item_id=?
        ''', (name, description, category_id, supplier_id, unit_price, reorder_level, item_id))
        conn.commit()
        conn.close()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('inventory'))

    categories = conn.execute('SELECT * FROM Categories').fetchall()
    suppliers = conn.execute('SELECT * FROM Suppliers').fetchall()
    conn.close()
    return render_template('edit_inventory.html', item=item, categories=categories, suppliers=suppliers)

@app.route('/inventory/delete/<int:item_id>')
def delete_item(item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Items WHERE item_id = ?', (item_id,))
    conn.commit()
    conn.close()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('inventory'))

@app.route('/suppliers/add', methods=['GET', 'POST'])
def add_supplier():
    conn = get_db_connection()

    if request.method == 'POST':
        supplier_name = request.form['supplier_name']
        contact_person = request.form['contact_person']
        phone = request.form['phone']
        email = request.form['email']

        conn.execute('''
            INSERT INTO Suppliers (supplier_name, contact_person, phone, email)
            VALUES (?, ?, ?, ?)
        ''', (supplier_name, contact_person, phone, email))

        conn.commit()
        conn.close()

        flash('New supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))

    conn.close()
    return render_template('add_supplier.html')

@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    conn = get_db_connection()
    supplier = conn.execute('SELECT * FROM Suppliers WHERE supplier_id = ?', (supplier_id,)).fetchone()

    if not supplier:
        conn.close()
        flash('Supplier not found.', 'danger')
        return redirect(url_for('suppliers'))

    if request.method == 'POST':
        supplier_name = request.form['supplier_name']
        contact_person = request.form['contact_person']
        phone = request.form['phone']
        email = request.form['email']

        conn.execute('''
            UPDATE Suppliers
            SET supplier_name=?, contact_person=?, phone=?, email=?, updated_at=CURRENT_TIMESTAMP
            WHERE supplier_id=?
        ''', (supplier_name, contact_person, phone, email, supplier_id))

        conn.commit()
        conn.close()
        flash('Supplier updated successfully!', 'success')
        return redirect(url_for('suppliers'))

    conn.close()
    return render_template('edit_supplier.html', supplier=supplier)

@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
def delete_supplier(supplier_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Suppliers WHERE supplier_id = ?', (supplier_id,))
    conn.commit()
    conn.close()
    flash('Supplier deleted successfully!', 'success')
    return redirect(url_for('suppliers'))

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password_hash = request.form['password']
        role = request.form['role']
        email = request.form['email']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO Users (username, password_hash, role, email)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, role, email))
        conn.commit()
        conn.close()

        flash('User added successfully!', 'success')
        return redirect(url_for('settings'))

    return render_template('add_user.html')

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,)).fetchone()

    if not user:
        conn.close()
        flash('User not found.', 'danger')
        return redirect(url_for('settings'))

    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        email = request.form['email']

        conn.execute('''
            UPDATE Users
            SET username=?, role=?, email=?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (username, role, email, user_id))
        conn.commit()
        conn.close()

        flash('User updated successfully!', 'success')
        return redirect(url_for('settings'))

    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('settings'))

if __name__ == '__main__':
    app.run(debug=True)
    