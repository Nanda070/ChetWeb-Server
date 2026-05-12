import sqlite3
import os

# Статичные настройки (Токен остается в коде или выносится в .env бота)
TOKEN = 'MTUwMzQxOTAyOTAyNzU1NzQyNg.Gu20t7.sibvCfvvxUyohcLORbBHgoKPiEzyWYREwpN7GQ'

# Абсолютный путь к единой БД Dashboard
DB_PATH = r"C:\Users\adnan\source\repos\404srv\404_system.db"

def get_dynamic_value(key: str, default_value):
    """Прямой запрос к базе данных при каждом вызове переменной."""
    if not os.path.exists(DB_PATH):
        return default_value
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM global_config WHERE key=?", (key,))
            row = cursor.fetchone()
            if row:
                # Возвращаем int, если значение состоит только из цифр (ID ролей/каналов)
                return int(row[0]) if row[0].isdigit() else row[0]
    except Exception as e:
        print(f"[Конфиг] Ошибка чтения {key} из БД: {e}")
        pass
    return default_value

# Динамический перехват атрибутов (Python 3.7+)
def __getattr__(name):
    """
    Вызывается автоматически каждый раз, когда код бота запрашивает config.NAME.
    Обеспечивает мгновенное применение настроек из веб-панели без перезагрузки бота.
    """
    defaults = {
        "TARGET_ROLE_ID": 1503414541206290673,
        "VOICE_CHANNEL_ID": 1503414991842185296,
        "LOG_CHANNEL_ID": 1503425312409780344
    }
    
    if name in defaults:
        return get_dynamic_value(name, defaults[name])
        
    raise AttributeError(f"Модуль 'config' не содержит атрибута '{name}'")