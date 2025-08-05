from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'mov'}

# Check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        socialId TEXT,
        category TEXT,
        timestamp REAL,
        file_path TEXT,
        likes INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

# Clean old ads (older than 7 days)
def clean_old_ads():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    seven_days_ago = time.time() - (7 * 24 * 60 * 60)
    c.execute('DELETE FROM ads WHERE timestamp < ?', (seven_days_ago,))
    conn.commit()
    conn.close()

# Create directories
os.makedirs('hidden', exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if not os.path.exists('hidden/global_message.txt'):
    with open('hidden/global_message.txt', 'w', encoding='utf-8') as f:
        f.write('پیام همگانی نمونه')

init_db()
clean_old_ads()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ads', methods=['GET'])
def get_ads():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, description, socialId, category, timestamp, file_path, likes FROM ads')
    ads = [{'id': row[0], 'description': row[1], 'socialId': row[2], 'category': row[3], 'timestamp': row[4], 'file_path': row[5], 'likes': row[6]} for row in c.fetchall()]
    conn.close()
    return jsonify(ads)

@app.route('/api/ads', methods=['POST'])
def add_ad():
    if 'file' not in request.files:
        return jsonify({'error': 'فایل اجباری است'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'فایلی انتخاب نشده است'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        data = request.form
        description = data.get('description')
        socialId = data.get('socialId')
        category = data.get('category')
        
        if not socialId:
            return jsonify({'error': 'آیدی تلگرام یا اینستاگرام اجباری است'}), 400
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO ads (description, socialId, category, timestamp, file_path) VALUES (?, ?, ?, ?, ?)',
                  (description, socialId, category, time.time(), filename))
        conn.commit()
        conn.close()
        clean_old_ads()
        return jsonify({'message': 'آگهی با موفقیت ثبت شد', 'file_path': filename}), 201
    return jsonify({'error': 'فرمت فایل پشتیبانی نمی‌شود'}), 400

@app.route('/api/ads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

@app.route('/api/like/<int:ad_id>', methods=['POST'])
def like_ad(ad_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE ads SET likes = likes + 1 WHERE id = ?', (ad_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'لایک اضافه شد'})

if __name__ == '__main__':
    app.run(debug=True)
