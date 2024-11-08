# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3  # SQLite for lightweight database
from datetime import datetime  # To track when items are used

# Create the Flask app instance
app = Flask(__name__)

# Secret key for session management (needed for session and flash functionality)
app.secret_key = 'your_secret_key'

# Mock admin credentials (this is a simple setup, consider using hashed passwords later)
users = {
    'administrator': {'password': 'localhost', 'role': 'admin'},
    'dev': {'password': 'server-development', 'role': 'admin'},
    'greg': {'password': 'greg', 'role': 'user'},
    'linda': {'password': 'linda', 'role': 'user'},
}

# Function to connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

############################################
# ROUTE: Home/Index Page (List all items)  #
############################################
@app.route('/')
def index():
    # Connect to the database
    conn = connect_db()

   # Fetch all items to display on the homepage
    items = conn.execute('SELECT * FROM inventory').fetchall()
    
    # Debugging: Print the items to see what's being returned
    print(f"Items fetched from DB: {items}")
    
    conn.close()

    # Check if items are fetched properly
    if items is None:
        print("Error: Items is None")
    
    return render_template('index.html', items=items)

########################
# ROUTE: Admin Login    #
########################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username exists and the password matches
        if username in users and users[username]['password'] == password:
            session['user_id'] = username  # Store username in session
            session['is_admin'] = (users[username]['role'] == 'admin')  # Set admin status
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

########################
# ROUTE: Admin Logout   #
########################
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

###################################
# ROUTE: Add New Item (Admin Only) #
###################################
@app.route('/add', methods=['GET', 'POST'])
def add_item():
    # Check if the user is logged in as admin
    if 'is_admin' not in session:
        flash('You need to be logged in as an admin to add items.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get item details from the form
        name = request.form['name']
        quantity = request.form['quantity']
        expiry_date = request.form['expiry_date']
        min_quantity = request.form['min_quantity']

        # Connect to the database and insert the new item
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO inventory (name, quantity, expiry_date, min_quantity, last_used) VALUES (?, ?, ?, ?, ?)',
                       (name, quantity, expiry_date, min_quantity, None))
        conn.commit()
        conn.close()

        # Flash success message and redirect to the home page
        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))

    # Render the add item page
    return render_template('add.html')

######################################
# ROUTE: Mark Item as Used (Standard) #
######################################
@app.route('/use_item/<int:item_id>', methods=['GET', 'POST'])
def use_item(item_id):
    if 'user_id' not in session:  # Ensure user is logged in
        flash('Please log in to mark an item as used.', 'error')
        return redirect(url_for('login'))

    conn = connect_db()

    # Debugging: Print the item_id to ensure it's passed correctly
    print(f"Item ID received: {item_id}")
    
    # Fetch the item based on the item_id
    item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()

    if item:
        # Debugging: Print the item details for verification
        print(f"Item fetched from DB: {item['name']}, Quantity: {item['quantity']}")
        
        if item['quantity'] > 0:  # Only reduce if quantity is greater than 0
            new_quantity = item['quantity'] - 1
            conn.execute('UPDATE inventory SET quantity = ? WHERE id = ?', (new_quantity, item_id))
            conn.commit()
            flash(f'{item["name"]} marked as used. New quantity: {new_quantity}', 'success')
        else:
            flash('No items left to use!', 'error')
    else:
        # Debugging: Letting us know if the item is not found
        print(f"Item with ID {item_id} not found in the database.")
        flash('Item not found.', 'error')

    conn.close()
    return redirect(url_for('index'))


##############################################
# ROUTE: Undo "Item Used" Action (Admin Only) #
##############################################
@app.route('/undo_use/<int:item_id>', methods=['POST'])
def undo_use(item_id):
    # Check if the user is logged in as admin
    if 'is_admin' in session and session ['is_admin']:

        # Undo the "used" action by setting last_used back to NULL
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE inventory SET last_used = NULL WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()

        # Flash success message and redirect to the home page
        flash('Item use was successfully undone!', 'success')
    else:
        flash('You do not have permission to undo items.', 'error')
    return redirect(url_for('index'))

###########################################
# ROUTE: Delete Item In List (Admin Only) #
###########################################
@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    # Check if the user is an admin
    if 'is_admin' in session and session['is_admin']:
        try:
            # Connect to the database
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()

            # Execute the DELETE statement
            cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
            conn.commit()

            # Close the connection
            conn.close()

            flash('Item deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting item: {e}', 'error')
    else:
        flash('You are not authorized to delete items.', 'error')

    return redirect(url_for('index'))

###################################
# ROUTE: Reorder Report (Admin Only)
###################################
@app.route('/report')
def reorder_report():
    # Check if the user is logged in as admin
    if 'is_admin' not in session:
        flash('You need to be logged in as an admin to view the report.', 'error')
        return redirect(url_for('login'))

    # Fetch items that are below their minimum quantity (reorder report)
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE quantity < min_quantity')
    low_stock_items = cursor.fetchall()
    conn.close()

    # Render the reorder report page
    return render_template('report.html', items=low_stock_items)

############################################
# Manage User Accounts via Admin Dashboard #
############################################
@app.route('/admin/users')
def admin_users():
    if 'is_admin' in session and session['is_admin']:
        # Display a list of users or admin-specific content
        user_list = list(users.keys())
        return render_template('admin_users.html', users=user_list)
    else:
        flash('You do not have permission to access the admin panel.', 'error')
        return redirect(url_for('index'))

@app.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    # Check if the user is an admin
    if 'is_admin' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    
    # Get user details for display
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('reset_password', user_id=user_id))

        # Update the user password
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, user_id))  # Hash the password in production
        conn.commit()
        conn.close()
        flash('Password has been reset successfully!', 'success')
        return redirect(url_for('admin_users'))

    return render_template('reset_password.html', user_id=user_id, username=user['username'])


##############################
# RUN THE FLASK APP (Development Mode)
##############################
if __name__ == '__main__':
    # Run the app in development mode on localhost (Windows 11 will use http://localhost:5000)
    app.run(debug=True, host='0.0.0.0')

