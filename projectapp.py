from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import time

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        socialId TEXT,
        category TEXT,
        timestamp REAL
    )''')
    conn.commit()
    conn.close()

# Create hidden directory and sample global_message.txt if not exists
os.makedirs('hidden', exist_ok=True)
if not os.path.exists('hidden/global_message.txt'):
    with open('hidden/global_message.txt', 'w', encoding='utf-8') as f:
        f.write('پیام همگانی نمونه')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ads', methods=['GET'])
def get_ads():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, description, socialId, category FROM ads')
    ads = [{'id': row[0], 'description': row[1], 'socialId': row[2], 'category': row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(ads)

@app.route('/api/ads', methods=['POST'])
def add_ad():
    data = request.json
    description = data.get('description')
    socialId = data.get('socialId')
    category = data.get('category')
    
    if not socialId:
        return jsonify({'error': 'آیدی تلگرام یا اینستاگرام اجباری است'}), 400
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO ads (description, socialId, category, timestamp) VALUES (?, ?, ?, ?)',
              (description, socialId, category, time.time()))
    conn.commit()
    conn.close()
    return jsonify({'message': 'آگهی با موفقیت ثبت شد'}), 201

@app.route('/api/global_message', methods=['GET'])
def get_global_message():
    try:
        with open('hidden/global_message.txt', 'r', encoding='utf-8') as f:
            message = f.read()
        return jsonify({'message': message})
    except FileNotFoundError:
        return jsonify({'message': ''})

@app.route('/api/global_message', methods=['DELETE'])
def delete_global_message():
    try:
        os.remove('hidden/global_message.txt')
        return jsonify({'message': 'پیام حذف شد'})
    except FileNotFoundError:
        return jsonify({'message': 'فایلی وجود ندارد'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
