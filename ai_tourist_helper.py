import pandas as pd
import json
import os
from openai import OpenAI
from typing import Dict, List, Any
import re


class AITouristHelper:

    def __init__(self, data_path='cultural_objects_mnn.xlsx'):

        self.data_path = data_path
        self.locations_df = self._load_data()
        self.client = self._init_openrouter_client()

    def _load_data(self) -> pd.DataFrame:
        """Загрузка данных о культурных объектах"""
        try:
            df = pd.read_excel(self.data_path)
            print(f"Загружено {len(df)} культурных объектов")
            return df
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return pd.DataFrame()

    def _init_openrouter_client(self) -> OpenAI:
        """Инициализация клиента OpenRouter API"""
        api_key = os.environ.get('OPENROUTER_API_KEY')

        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY не установлен!\n"
                "Получите ключ на: https://openrouter.ai/keys\n"
                "Установите: export OPENROUTER_API_KEY='your-key'"
            )

        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def get_locations_count(self) -> int:
        """Получить количество доступных локаций"""
        return len(self.locations_df)

    def _prepare_locations_context(self) -> str:
        """
        Подготовить контекст с информацией о доступных локациях
        """
        locations_info = []

        for idx, row in self.locations_df.iterrows():
            location = {
                'id': row['id'],
                'название': row['title'],
                'адрес': row['address'],
                'описание': row['description'][:500] if pd.notna(row['description']) else 'Описание отсутствует',
                'координаты': row['coordinate'] if pd.notna(row['coordinate']) else 'Не указаны'
            }
            locations_info.append(location)

        return json.dumps(locations_info, ensure_ascii=False, indent=2)

    def generate_personalized_route(
            self,
            interests: str,
            time_hours: float,
            current_location: str
    ) -> Dict[str, Any]:

        locations_context = self._prepare_locations_context()

        system_prompt = """Ты - экспертный AI-помощник туриста по Нижнему Новгороду. 
Твоя задача - создать персональный маршрут прогулки на основе интересов пользователя.

ВАЖНЫЕ ПРАВИЛА:
1. Выбери от 3 до 5 реальных мест из предоставленного списка
2. Места должны соответствовать интересам пользователя
3. Учитывай доступное время и расстояния между объектами
4. Для каждого места объясни, ПОЧЕМУ оно включено в маршрут
5. Предложи оптимальный порядок посещения
6. Укажи примерное время на каждую локацию
7. Отвечай СТРОГО в формате JSON

ФОРМАТ ОТВЕТА (JSON):
{
  "маршрут": [
    {
      "порядок": 1,
      "название": "Название места",
      "адрес": "Адрес",
      "время_посещения_минут": 30,
      "почему_выбрано": "Детальное объяснение выбора",
      "что_посмотреть": "Что конкретно посмотреть/сделать"
    }
  ],
  "общее_описание": "Краткое описание всего маршрута",
  "советы": ["Совет 1", "Совет 2"],
  "общее_время_минут": 180,
  "категории_интересов": ["категория1", "категория2"]
}"""

        user_prompt = f"""
Интересы пользователя: {interests}
Доступное время: {time_hours} часов
Текущее местоположение: {current_location}

ДОСТУПНЫЕ ЛОКАЦИИ В НИЖНЕМ НОВГОРОДЕ:
{locations_context}

Создай персональный маршрут прогулки, учитывая интересы пользователя и доступное время.
Верни ответ ТОЛЬКО в формате JSON, без дополнительного текста."""

        try:
            response = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "AI Tourist Helper NN",
                },
                model="openai/gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            ai_response = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_response = json_match.group(0)
            route_data = json.loads(ai_response)

            route_data['успешно'] = True
            route_data['запрос'] = {
                'интересы': interests,
                'время_часов': time_hours,
                'местоположение': current_location
            }

            return route_data

        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            print(f"Ответ AI: {ai_response}")
            return {
                'успешно': False,
                'ошибка': 'Не удалось распарсить ответ AI',
                'сырой_ответ': ai_response
            }

        except Exception as e:
            print(f"Ошибка генерации маршрута: {e}")
            return {
                'успешно': False,
                'ошибка': str(e)
            }

    def get_location_by_id(self, location_id: int) -> Dict:
        """Получить информацию о локации по ID"""
        location = self.locations_df[self.locations_df['id'] == location_id]
        if not location.empty:
            return location.iloc[0].to_dict()
        return None