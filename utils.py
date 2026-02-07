import hmac
import hashlib
import time
import json
import random

class TelegramAuth:
    @staticmethod
    def validate_init_data(init_ str, bot_token: str) -> bool:
        try:
            params = {}
            for item in init_data.split('&'):
                if '=' in item:
                    key, value = item.split('=', 1)
                    params[key] = value
            
            if 'hash' not in params:
                return False
            
            received_hash = params.pop('hash')
            
            data_check_string = '\n'.join(
                f"{k}={v}" for k, v in sorted(params.items())
            )
            
            secret_key = hmac.new(
                b"WebAppData",
                bot_token.encode(),
                hashlib.sha256
            ).digest()
            
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if calculated_hash != received_hash:
                return False
            
            auth_date = int(params.get('auth_date', 0))
            if time.time() - auth_date > 86400:
                return False
            
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    @staticmethod
    def parse_user_data(init_ str):
        try:
            params = {}
            for item in init_data.split('&'):
                if '=' in item:
                    key, value = item.split('=', 1)
                    params[key] = value
            
            user_data = json.loads(params.get('user', '{}'))
            return user_data
        except:
            return {}

class GameLogic:
    @staticmethod
    def generate_result(rare_chance=0.10):
        rand = random.random()
        
        if rand < rare_chance:
            number = random.randint(16, 20)
            win_type = 'rare'
            reward_egp = number * 10
            reward_ton = number * 0.00025
            reward_usdt = number * 0.32
        else:
            number = random.randint(1, 5)
            win_type = 'normal'
            reward_egp = number * 2
            reward_ton = number * 0.00005
            reward_usdt = number * 0.064
        
        return {
            'number': number,
            'win_type': win_type,
            'reward_egp': reward_egp,
            'reward_ton': reward_ton,
            'reward_usdt': reward_usdt
        }