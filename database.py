from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, init_default_settings, generate_referral_code, User, Referral, GameLog, Withdrawal, PromoCode, PromoCodeUsage, Task, TaskCompletion, Advertisement, AdView, Setting
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, database_url='sqlite:///game.db'):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        session = self.Session()
        init_default_settings(session)
        session.close()
    
    def get_session(self):
        return self.Session()
    
    def create_user(self, telegram_id, username=None, first_name=None, last_name=None, 
                   photo_url=None, referred_by=None):
        session = self.Session()
        
        existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if existing_user:
            session.close()
            return self.get_user(telegram_id)
        
        referral_code = generate_referral_code()
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url,
            referral_code=referral_code,
            referred_by=referred_by
        )
        
        session.add(user)
        session.commit()
        
        if referred_by and referred_by != telegram_id:
            referral = Referral(
                inviter_id=referred_by,
                invited_id=telegram_id,
                status='completed'
            )
            session.add(referral)
            session.commit()
            
            self.check_referral_reward(referred_by, session)
        
        session.close()
        return self.get_user(telegram_id)
    
    def get_user(self, telegram_id):
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        session.close()
        
        if user:
            return {
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'photo_url': user.photo_url,
                'referral_code': user.referral_code,
                'referred_by': user.referred_by,
                'invites_count': user.invites_count,
                'games_available': user.games_available,
                'total_games': user.total_games,
                'wins': user.wins,
                'rare_wins': user.rare_wins,
                'balance_egp': float(user.balance_egp),
                'balance_ton': float(user.balance_ton),
                'balance_usdt': float(user.balance_usdt),
                'total_earnings_egp': float(user.total_earnings_egp),
                'total_earnings_ton': float(user.total_earnings_ton),
                'total_earnings_usdt': float(user.total_earnings_usdt),
                'join_date': user.join_date,
                'last_login': user.last_login,
                'is_banned': user.is_banned,
                'is_premium': user.is_premium,
                'phone_number': user.phone_number,
                'payment_method': user.payment_method,
                'wallet_address': user.wallet_address,
                'completed_tasks': user.completed_tasks
            }
        return None
    
    def update_user(self, telegram_id, **kwargs):
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.last_login = datetime.utcnow()
            session.commit()
        
        session.close()
    
    def use_game(self, telegram_id):
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if user and user.games_available > 0 and not user.is_banned:
            user.games_available -= 1
            user.total_games += 1
            session.commit()
            session.close()
            return True
        
        session.close()
        return False
    
    def add_games(self, telegram_id, count=1):
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if user:
            user.games_available += count
            session.commit()
        
        session.close()
    
    def add_balance(self, telegram_id, amount, currency='EGP'):
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if user:
            if currency == 'EGP':
                user.balance_egp += amount
                user.total_earnings_egp += amount
            elif currency == 'TON':
                user.balance_ton += amount
                user.total_earnings_ton += amount
            elif currency == 'USDT':
                user.balance_usdt += amount
                user.total_earnings_usdt += amount
            session.commit()
        
        session.close()
    
    def record_game(self, user_id, result_number, win_type, reward_egp=0, reward_ton=0, reward_usdt=0):
        session = self.Session()
        
        game_log = GameLog(
            user_id=user_id,
            result_number=result_number,
            win_type=win_type,
            reward_egp=reward_egp,
            reward_ton=reward_ton,
            reward_usdt=reward_usdt
        )
        session.add(game_log)
        
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            user.wins += 1
            if win_type == 'rare':
                user.rare_wins += 1
            
            user.balance_egp += reward_egp
            user.balance_ton += reward_ton
            user.balance_usdt += reward_usdt
            
            user.total_earnings_egp += reward_egp
            user.total_earnings_ton += reward_ton
            user.total_earnings_usdt += reward_usdt
        
        session.commit()
        session.close()
    
    def check_referral_reward(self, inviter_id, session=None):
        should_close = False
        if session is None:
            session = self.Session()
            should_close = True
        
        threshold_setting = session.query(Setting).filter_by(key='referral_threshold').first()
        threshold = int(threshold_setting.value) if threshold_setting else 3
        
        reward_setting = session.query(Setting).filter_by(key='referral_reward').first()
        reward_games = int(reward_setting.value) if reward_setting else 1
        
        count = session.query(Referral).filter_by(
            inviter_id=inviter_id,
            status='completed'
        ).count()
        
        if count >= threshold and count % threshold == 0:
            user = session.query(User).filter_by(telegram_id=inviter_id).first()
            if user:
                user.games_available += reward_games
                user.invites_count += 1
                
                reward_log = GameLog(
                    user_id=inviter_id,
                    result_number=0,
                    win_type='referral_reward',
                    reward_egp=0
                )
                session.add(reward_log)
                session.commit()
        
        if should_close:
            session.close()
    
    def create_withdrawal(self, user_id, amount, currency, payment_method, phone_number, wallet_address=None):
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=user_id).first()
        
        if not user:
            session.close()
            return False, "User not found"
        
        if currency == 'EGP' and user.balance_egp < amount:
            session.close()
            return False, "رصيد غير كافي"
        elif currency == 'TON' and user.balance_ton < amount:
            session.close()
            return False, "رصيد غير كافي"
        elif currency == 'USDT' and user.balance_usdt < amount:
            session.close()
            return False, "رصيد غير كافي"
        
        withdrawal = Withdrawal(
            user_id=user_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            phone_number=phone_number,
            wallet_address=wallet_address,
            status='pending'
        )
        session.add(withdrawal)
        session.commit()
        
        withdrawal_id = withdrawal.id
        session.close()
        
        return True, withdrawal_id
    
    def get_user_withdrawals(self, user_id):
        session = self.Session()
        withdrawals = session.query(Withdrawal).filter_by(user_id=user_id).order_by(
            Withdrawal.created_at.desc()
        ).all()
        
        result = [{
            'id': w.id,
            'amount': float(w.amount),
            'currency': w.currency,
            'payment_method': w.payment_method,
            'phone_number': w.phone_number,
            'wallet_address': w.wallet_address,
            'status': w.status,
            'transaction_id': w.transaction_id,
            'created_at': w.created_at,
            'processed_at': w.processed_at,
            'notes': w.notes
        } for w in withdrawals]
        
        session.close()
        return result
    
    def create_promo_code(self, code, reward_type, reward_value, reward_currency='EGP', max_uses=100, days_valid=30):
        session = self.Session()
        
        expires_at = datetime.utcnow() + timedelta(days=days_valid)
        
        promo = PromoCode(
            code=code.upper(),
            reward_type=reward_type,
            reward_value=reward_value,
            reward_currency=reward_currency,
            max_uses=max_uses,
            expires_at=expires_at,
            is_active=True
        )
        
        session.add(promo)
        session.commit()
        session.close()
    
    def use_promo_code(self, user_id, promo_code):
        session = self.Session()
        
        promo = session.query(PromoCode).filter_by(code=promo_code.upper(), is_active=True).first()
        
        if not promo:
            session.close()
            return False, "الرمز غير صحيح أو منتهي الصلاحية"
        
        existing = session.query(PromoCodeUsage).filter_by(
            user_id=user_id,
            promo_code_id=promo.id
        ).first()
        
        if existing:
            session.close()
            return False, "لقد استخدمت هذا الرمز من قبل"
        
        if promo.expires_at and promo.expires_at < datetime.utcnow():
            session.close()
            return False, "الرمز منتهي الصلاحية"
        
        if promo.used_count >= promo.max_uses:
            session.close()
            return False, "تم استخدام الرمز بالكامل"
        
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            if promo.reward_type == 'games':
                user.games_available += int(promo.reward_value)
            elif promo.reward_type == 'balance':
                if promo.reward_currency == 'EGP':
                    user.balance_egp += float(promo.reward_value)
                    user.total_earnings_egp += float(promo.reward_value)
                elif promo.reward_currency == 'TON':
                    user.balance_ton += float(promo.reward_value)
                    user.total_earnings_ton += float(promo.reward_value)
                elif promo.reward_currency == 'USDT':
                    user.balance_usdt += float(promo.reward_value)
                    user.total_earnings_usdt += float(promo.reward_value)
            elif promo.reward_type == 'premium':
                user.is_premium = True
            
            usage = PromoCodeUsage(
                promo_code_id=promo.id,
                user_id=user_id,
                reward_received=promo.reward_value
            )
            session.add(usage)
            
            promo.used_count += 1
            
            session.commit()
            session.close()
            
            return True, f"تم تفعيل الرمز بنجاح! حصلت على {promo.reward_value} {promo.reward_type}"
        
        session.close()
        return False, "حدث خطأ"
    
    def get_leaderboard(self, limit=10):
        session = self.Session()
        users = session.query(User).filter_by(is_banned=False).order_by(
            User.rare_wins.desc(),
            User.wins.desc()
        ).limit(limit).all()
        
        result = [{
            'telegram_id': u.telegram_id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'rare_wins': u.rare_wins,
            'wins': u.wins,
            'total_games': u.total_games,
            'balance_egp': float(u.balance_egp),
            'balance_ton': float(u.balance_ton),
            'balance_usdt': float(u.balance_usdt)
        } for u in users]
        
        session.close()
        return result
    
    def get_total_stats(self):
        session = self.Session()
        
        stats = {
            'total_users': session.query(User).count(),
            'total_games': session.query(GameLog).count(),
            'total_wins': session.query(GameLog).filter(GameLog.win_type.in_(['normal', 'rare'])).count(),
            'total_rare_wins': session.query(GameLog).filter_by(win_type='rare').count(),
            'total_referrals': session.query(Referral).count(),
            'total_withdrawals': session.query(Withdrawal).filter_by(status='completed').count(),
        }
        
        session.close()
        return stats
    
    def create_task(self, task_id, title, description, reward_egp=0, reward_ton=0, reward_usdt=0, reward_games=0, task_type='manual', verification_data=None, required_count=1):
        session = self.Session()
        
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            reward_egp=reward_egp,
            reward_ton=reward_ton,
            reward_usdt=reward_usdt,
            reward_games=reward_games,
            task_type=task_type,
            verification_data=verification_data or {},
            required_count=required_count,
            is_active=True
        )
        
        session.add(task)
        session.commit()
        session.close()
    
    def get_active_tasks(self):
        session = self.Session()
        tasks = session.query(Task).filter_by(is_active=True).order_by(Task.order).all()
        
        result = [{
            'id': t.id,
            'task_id': t.task_id,
            'title': t.title,
            'description': t.description,
            'reward_egp': float(t.reward_egp),
            'reward_ton': float(t.reward_ton),
            'reward_usdt': float(t.reward_usdt),
            'reward_games': t.reward_games,
            'task_type': t.task_type,
            'verification_data': t.verification_data,
            'required_count': t.required_count
        } for t in tasks]
        
        session.close()
        return result
    
    def complete_task(self, user_id, task_id):
        session = self.Session()
        
        task = session.query(Task).filter_by(id=task_id, is_active=True).first()
        if not task:
            session.close()
            return False, "المهمة غير موجودة"
        
        existing = session.query(TaskCompletion).filter_by(
            user_id=user_id,
            task_id=task_id
        ).first()
        
        if existing:
            session.close()
            return False, "لقد أكملت هذه المهمة من قبل"
        
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            if task.reward_games > 0:
                user.games_available += task.reward_games
            
            if task.reward_egp > 0:
                user.balance_egp += task.reward_egp
                user.total_earnings_egp += task.reward_egp
            
            if task.reward_ton > 0:
                user.balance_ton += task.reward_ton
                user.total_earnings_ton += task.reward_ton
            
            if task.reward_usdt > 0:
                user.balance_usdt += task.reward_usdt
                user.total_earnings_usdt += task.reward_usdt
            
            user.completed_tasks += 1
            
            completion = TaskCompletion(
                task_id=task_id,
                user_id=user_id,
                status='completed',
                reward_egp=task.reward_egp,
                reward_ton=task.reward_ton,
                reward_usdt=task.reward_usdt
            )
            session.add(completion)
            
            session.commit()
            session.close()
            
            return True, "تم إكمال المهمة بنجاح!"
        
        session.close()
        return False, "حدث خطأ"
    
    def create_advertisement(self, ad_code, title, reward_egp=0, reward_ton=0, reward_usdt=0, reward_games=0, required_views=1, max_daily_views=10, days_valid=7):
        session = self.Session()
        
        expires_at = datetime.utcnow() + timedelta(days=days_valid)
        
        ad = Advertisement(
            ad_code=ad_code,
            title=title,
            reward_egp=reward_egp,
            reward_ton=reward_ton,
            reward_usdt=reward_usdt,
            reward_games=reward_games,
            required_views=required_views,
            max_daily_views=max_daily_views,
            is_active=True,
            expires_at=expires_at
        )
        
        session.add(ad)
        session.commit()
        session.close()
    
    def get_active_ads(self):
        session = self.Session()
        ads = session.query(Advertisement).filter_by(is_active=True).filter(
            Advertisement.expires_at > datetime.utcnow()
        ).all()
        
        result = [{
            'id': a.id,
            'ad_code': a.ad_code,
            'title': a.title,
            'reward_egp': float(a.reward_egp),
            'reward_ton': float(a.reward_ton),
            'reward_usdt': float(a.reward_usdt),
            'reward_games': a.reward_games,
            'required_views': a.required_views,
            'max_daily_views': a.max_daily_views
        } for a in ads]
        
        session.close()
        return result
    
    def record_ad_view(self, user_id, ad_id):
        session = self.Session()
        
        ad = session.query(Advertisement).filter_by(id=ad_id, is_active=True).first()
        if not ad:
            session.close()
            return False, "الإعلان غير موجود"
        
        today = datetime.utcnow().date()
        views_today = session.query(AdView).filter_by(
            user_id=user_id,
            ad_id=ad_id
        ).filter(
            func.date(AdView.viewed_at) == today
        ).count()
        
        if views_today >= ad.max_daily_views:
            session.close()
            return False, "لقد وصلت للحد الأقصى من المشاهدات اليومية"
        
        view = AdView(
            ad_id=ad_id,
            user_id=user_id,
            rewarded=False
        )
        session.add(view)
        session.commit()
        
        view_id = view.id
        session.close()
        
        return True, view_id
    
    def reward_ad_view(self, view_id):
        session = self.Session()
        
        view = session.query(AdView).filter_by(id=view_id, rewarded=False).first()
        if not view:
            session.close()
            return False
        
        ad = session.query(Advertisement).filter_by(id=view.ad_id).first()
        user = session.query(User).filter_by(teleg