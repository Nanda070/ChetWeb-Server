from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from database import Base

class GlobalConfig(Base):
    """Таблица для хранения настроек (ID каналов, ролей и т.д.)"""
    __tablename__ = "global_config"
    
    key = Column(String, primary_key=True, index=True)  # Например: 'TARGET_ROLE_ID'
    value = Column(String, nullable=False)              # Значение: '1503414541206290673'
    description = Column(String, nullable=True)         # Описание для веба

class AuditLog(Base):
    """Единая лента логов для всех ботов (Global Audit Trail)"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source_bot = Column(String, index=True)             # ChetBot, ChetVoice, ChetSupply
    action = Column(String, nullable=False)             # Что произошло
    user_id = Column(String, index=True)                # Discord ID инициатора
    details = Column(Text, nullable=True)               # Подробности (JSON или текст)
    timestamp = Column(DateTime, default=datetime.utcnow)

class FeedbackCase(Base):
    """CRM для жалоб и предложений"""
    __tablename__ = "feedback_cases"
    
    case_id = Column(String, primary_key=True, index=True) # PR-0001
    category = Column(String, index=True)                  # players, admins, candidate
    submitter_id = Column(String, nullable=False)          # Кто подал
    status = Column(String, default="pending")             # pending, approved, denied
    reviewer_id = Column(String, nullable=True)            # Кто рассмотрел
    created_at = Column(DateTime, default=datetime.utcnow)