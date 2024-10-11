from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Get the database path from an environment variable, or use a default path
DATABASE_DIR = os.environ.get('DATABASE_DIR', '/app')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'payments.db')

# Ensure that the 'payments_data' directory exists
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This helps to return rows as dictionaries
    return conn

# Initialize the database (Create payments table if it doesn't exist)
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Create a new payment
@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()

    # Validate incoming data
    if not data or not data.get('order_id') or not data.get('amount'):
        return jsonify({"error": "Order ID and amount are required"}), 400

    # Insert the new payment into the database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO payments (order_id, amount, status, created_at)
        VALUES (?, ?, ?, ?)
    ''', (data['order_id'], data['amount'], 'pending', datetime.utcnow().isoformat()))
    conn.commit()
    payment_id = cur.lastrowid
    conn.close()

    return jsonify({
        'payment_id': payment_id,
        'order_id': data['order_id'],
        'amount': data['amount'],
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    }), 201

# Get details of a specific payment
@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    conn = get_db_connection()
    payment = conn.execute('SELECT * FROM payments WHERE id = ?', (payment_id,)).fetchone()
    conn.close()

    if payment is None:
        return jsonify({"error": "Payment not found"}), 404

    return jsonify({
        'payment_id': payment['id'],
        'order_id': payment['order_id'],
        'amount': payment['amount'],
        'status': payment['status'],
        'created_at': payment['created_at']
    })

# Update the status of a payment
@app.route('/payments/<int:payment_id>/status', methods=['PUT'])
def update_payment_status(payment_id):
    data = request.get_json()

    if not data or not data.get('status'):
        return jsonify({"error": "Status is required"}), 400

    conn = get_db_connection()
    payment = conn.execute('SELECT * FROM payments WHERE id = ?', (payment_id,)).fetchone()

    if payment is None:
        conn.close()
        return jsonify({"error": "Payment not found"}), 404

    conn.execute('UPDATE payments SET status = ? WHERE id = ?', (data['status'], payment_id))
    conn.commit()
    conn.close()

    return jsonify({
        'payment_id': payment_id,
        'order_id': payment['order_id'],
        'amount': payment['amount'],
        'status': data['status'],
        'created_at': payment['created_at']
    }), 200

# Run the app
if __name__ == '__main__':
    init_db()  # Ensure the database is initialized before running
    app.run(host='0.0.0.0', port=5001)
