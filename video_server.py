#!/usr/bin/env python3
import os
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Настройки для сохранения файлов
app.config['UPLOAD_FOLDER'] = 'videos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/api/process-video', methods=['POST'])
def process_video():
    try:
        if 'video' not in request.files or request.files['video'].filename == '':
            return jsonify({'error': 'Файл видео не выбран'}), 400
        
        file = request.files['video']
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
                'filepath': filepath,
                'size': file_size,
                'timestamp': request.form.get('timestamp'),
                'user_id': request.form.get('user_id')
            })
        else:
            return jsonify({'error': 'Ошибка сохранения файла'}), 500
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)