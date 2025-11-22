from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
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

@app.route('/inventory')
def inventory():
    conn = get_db_connection()
    items = conn.execute('''
        SELECT Items.item_id, Items.item_name, Items.description,
               Categories.category_name, Suppliers.supplier_name,
               Items.unit_price, Items.reorder_level,
               IFNULL(SUM(Stock.quantity), 0) AS total_stock
        FROM Items
        LEFT JOIN Categories ON Items.category_id = Categories.category_id
        LEFT JOIN Suppliers ON Items.supplier_id = Suppliers.supplier_id
        LEFT JOIN Stock ON Items.item_id = Stock.item_id
        GROUP BY Items.item_id
        ORDER BY Items.item_id
    ''').fetchall()
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

if __name__ == '__main__':
    app.run(debug=True)
