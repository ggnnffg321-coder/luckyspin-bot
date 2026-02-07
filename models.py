from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    photo_url = Column(String(500))
    referral_code = Column(String(20), unique=True, nullable=False)
    referred_by = Column(Integer, ForeignKey('users.telegram_id'), nullable=True)
    invites_count = Column(Integer, default=0)
    games_available = Column(Integer, default=1)
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    rare_wins = Column(Integer, default=0)
    balance_egp = Column(Float, default=0.0)
    balance_ton = Column(Float, default=0.0)
    balance_usdt = Column(Float, default=0.0)
    total_earnings_egp = Column(Float, default=0.0)
    total_earnings_ton = Column(Float, default=0.0)
    total_earnings_usdt = Column(Float, default=0.0)
    join_date = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_banned = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    phone_number = Column(String(20))
    payment_method = Column(String(50))
    wallet_address = Column(String(200))
    completed_tasks = Column(Integer, default=0)
    
    referrals = relationship("Referral", foreign_keys="[Referral.inviter_id]", back_populates="inviter")
    invited_by_user = relationship("User", remote_side=[telegram_id], backref="invited_users")
    withdrawals = relationship("Withdrawal", back_populates="user")
    promo_codes_used = relationship("PromoCodeUsage", back_populates="user")
    task_completions = relationship("TaskCompletion", back_populates="user")

class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    inviter_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    invited_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False, unique=True)
    status = Column(String(20), default='completed')
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="referrals")

class GameLog(Base):
    __tablename__ = 'game_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    result_number = Column(Integer, nullable=False)
    win_type = Column(String(50), nullable=False)
    reward_egp = Column(Float, default=0.0)
    reward_ton = Column(Float, default=0.0)
    reward_usdt = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class Withdrawal(Base):
    __tablename__ = 'withdrawals'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='EGP')
    payment_method = Column(String(50), nullable=False)
    phone_number = Column(String(20), nullable=False)
    wallet_address = Column(String(200))
    status = Column(String(20), default='pending')
    transaction_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    notes = Column(Text)
    
    user = relationship("User", back_populates="withdrawals")

class PromoCode(Base):
    __tablename__ = 'promo_codes'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    reward_type = Column(String(50), nullable=False)
    reward_value = Column(Float, nullable=False)
    reward_currency = Column(String(10), default='EGP')
    max_uses = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    usages = relationship("PromoCodeUsage", back_populates="promo_code")

class PromoCodeUsage(Base):
    __tablename__ = 'promo_code_usages'
    
    id = Column(Integer, primary_key=True)
    promo_code_id = Column(Integer, ForeignKey('promo_codes.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    reward_received = Column(Float)
    
    promo_code = relationship("PromoCode", back_populates="usages")
    user = relationship("User", back_populates="promo_codes_used")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reward_egp = Column(Float, default=0.0)
    reward_ton = Column(Float, default=0.0)
    reward_usdt = Column(Float, default=0.0)
    reward_games = Column(Integer, default=0)
    task_type = Column(String(50), nullable=False)
    verification_data = Column(JSON)
    required_count = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    completions = relationship("TaskCompletion", back_populates="task")

class TaskCompletion(Base):
    __tablename__ = 'task_completions'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    status = Column(String(20), default='completed')
    completed_at = Column(DateTime, default=datetime.utcnow)
    reward_egp = Column(Float, default=0.0)
    reward_ton = Column(Float, default=0.0)
    reward_usdt = Column(Float, default=0.0)
    
    task = relationship("Task", back_populates="completions")
    user = relationship("User", back_populates="task_completions")

class Advertisement(Base):
    __tablename__ = 'advertisements'
    
    id = Column(Integer, primary_key=True)
    ad_code = Column(Text, nullable=False)
    title = Column(String(200))
    reward_egp = Column(Float, default=0.0)
    reward_ton = Column(Float, default=0.0)
    reward_usdt = Column(Float, default=0.0)
    reward_games = Column(Integer, default=0)
    required_views = Column(Integer, default=1)
    max_daily_views = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    views = relationship("AdView", back_populates="advertisement")

class AdView(Base):
    __tablename__ = 'ad_views'
    
    id = Column(Integer, primary_key=True)
    ad_id = Column(Integer, ForeignKey('advertisements.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    rewarded = Column(Boolean, default=False)
    
    advertisement = relationship("Advertisement", back_populates="views")

class Setting(Base):
    __tablename__ = 'settings'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AdminLog(Base):
    __tablename__ = 'admin_logs'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db(database_url='sqlite:///game.db'):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

def init_default_settings(session):
    default_settings = {
        'rare_win_chance': '0.10',
        'normal_win_chance': '0.90',
        'referral_threshold': '3',
        'referral_reward': '1',
        'min_withdrawal': '100',
        'max_withdrawal': '5000',
        'promo_code_expiry_days': '30',
        'initial_games': '1',
        'withdrawal_enabled': 'true',
        'promo_system_enabled': 'true',
        'ad_system_enabled': 'true',
        'currency_egp_rate': '1.0',
        'currency_ton_rate': '0.000025',
        'currency_usdt_rate': '0.032'
    }
    
    for key, value in default_settings.items():
        setting = session.query(Setting).filter_by(key=key).first()
        if not setting:
            session.add(Setting(key=key, value=value))
    
    session.commit()

def generate_referral_code():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))