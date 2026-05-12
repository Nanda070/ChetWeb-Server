from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Подключаемся к локальному файлу 404_system.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./404_system.db"

# Движок базы данных (check_same_thread нужен только для SQLite в FastAPI)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Фабрика сессий (через нее мы будем читать и писать данные)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс, от которого мы будем наследовать наши таблицы
Base = declarative_base()

# Зависимость для FastAPI (открывает и закрывает подключение при каждом запросе)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()