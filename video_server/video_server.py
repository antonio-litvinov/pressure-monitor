#!/usr/bin/env python3
import os

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

token = os.environ.get("GIGADOC_TOKEN")

# Настройки для сохранения файлов
app.config['UPLOAD_FOLDER'] = 'videos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/upload', methods=['POST'])
def process_video():
    try:
        # Проверка Bearer токена
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Отсутствует или неверный Bearer токен'}), 401
        
        bearer_token = auth_header.split(' ')[1]
        if bearer_token != str(token):
            return jsonify({'error': 'Неверный токен авторизации'}), 401
        
        if 'file' not in request.files or request.files['file'].filename == '':
            return jsonify({'error': 'Файл видео не выбран'}), 400
        
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ Видео сохранено: {filename} ({file_size / 1024:.1f} КБ)")
            
            return jsonify({
                'success': True,
                'message': 'Видео получено и сохранено',
                'filename': filename,
            })
        else:
            return jsonify({'error': 'Ошибка сохранения файла'}), 500
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
