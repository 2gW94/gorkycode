from encoding_setup import setup_console_encoding
setup_console_encoding()

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from ai_tourist_helper import AITouristHelper

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Переменные из .env загружены")
except ImportError:
    print("python-dotenv не установлен")
except Exception as e:
    print(f"Ошибка при загрузке .env: {e}")

app = Flask(__name__)
CORS(app)

ai_helper = AITouristHelper()

@app.route('/')
def index():
    """Главная страница сайта"""
    return render_template('index.html')

@app.route('/api/generate_route', methods=['POST'])
def generate_route():
    """
    Обрабатываем запрос от пользователя на создание персонального маршрута
    
    Ожидаем JSON с интересами, временем и местом старта
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Данные не получены'}), 400

        interests = data.get('interests', ' ').strip()
        time_hours = data.get('time_hours')
        location = data.get('location', '').strip()

        if not interests:
            return jsonify({'error': 'Пожалуйста, укажите ваши интересы'}), 400
        
        if not time_hours:
            return jsonify({'error': 'Пожалуйста, укажите сколько у вас времени'}), 400

        try:
            time_hours = float(time_hours)
            if time_hours <= 0 or time_hours > 24:
                return jsonify({'error': 'Время должно быть от 0.5 до 24 часов'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Неверный формат времени'}), 400

        if not location:
            return jsonify({'error': 'Пожалуйста, укажите ваше текущее место'}), 400

        result = ai_helper.generate_personalized_route(
            interests=interests,
            time_hours=time_hours,
            current_location=location
        )

        return jsonify(result)

    except Exception as e:
        print(f"Ошибка при создании маршрута: {str(e)}")
        return jsonify({'error': f'Произошла ошибка: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверяем, что сервис работает и доступен"""
    return jsonify({
        'status': 'ok',
        'service': 'AI Tourist Helper',
        'locations_count': ai_helper.get_locations_count()
    })

if __name__ == '__main__':
    if not os.environ.get('OPENROUTER_API_KEY'):
        print("Не установлен OPENROUTER_API_KEY")
        print("Установите ключ командой: export OPENROUTER_API_KEY='ваш-ключ'")

    print("Запуск AI-помощника туриста...")
    print(f"Загружено локаций: {ai_helper.get_locations_count()}")
    print("Сервис доступен по адресу: http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)
