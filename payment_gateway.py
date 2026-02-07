import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class PaymentGateway:
    """Payment gateway for Tounes and Fawry Cash"""
    
    def __init__(self):
        self.api_key = os.getenv('PAYMENT_API_KEY', '')
        self.secret_key = os.getenv('PAYMENT_SECRET_KEY', '')
        self.base_url = "https://api.payment-gateway.com"  # Replace with actual API
    
    def validate_phone(self, phone_number, payment_method):
        """Validate phone number format"""
        phone = phone_number.strip()
        
        if payment_method == 'tounes':
            # Tounes format: 2010XXXXXXXX, 2011XXXXXXXX, etc.
            return phone.startswith(('2010', '2011', '2012', '2015')) and len(phone) == 11
        elif payment_method == 'fawry':
            # Fawry Cash format
            return phone.startswith(('2010', '2011', '2012', '2015')) and len(phone) == 11
        return False
    
    def process_withdrawal(self, amount, phone_number, payment_method, user_id):
        """
        Process withdrawal request
        Returns: (success, transaction_id/error_message)
        """
        try:
            # Validate amount
            min_withdrawal = float(os.getenv('MIN_WITHDRAWAL', 100))
            max_withdrawal = float(os.getenv('MAX_WITHDRAWAL', 5000))
            
            if amount < min_withdrawal:
                return False, f"الحد الأدنى للسحب هو {min_withdrawal} جنيه"
            
            if amount > max_withdrawal:
                return False, f"الحد الأقصى للسحب هو {max_withdrawal} جنيه"
            
            # Validate phone
            if not self.validate_phone(phone_number, payment_method):
                return False, "رقم الهاتف غير صحيح"
            
            # For demo purposes - in production, integrate with actual payment API
            # Here we simulate a successful transaction
            transaction_id = f"TXN{user_id}{int(datetime.now().timestamp())}"
            
            # TODO: Integrate with actual payment API
            # Example for Tounes:
            # response = requests.post(f"{self.base_url}/tounes/withdraw", json={
            #     'api_key': self.api_key,
            #     'secret_key': self.secret_key,
            #     'amount': amount,
            #     'phone': phone_number,
            #     'reference': transaction_id
            # })
            
            # Simulate success
            return True, transaction_id
            
        except Exception as e:
            print(f"Payment error: {e}")
            return False, "حدث خطأ في معالجة السحب"
    
    def get_payment_methods(self):
        """Return available payment methods"""
        return [
            {
                'id': 'tounes',
                'name': 'تونز كاش',
                'icon': '💳',
                'min_amount': float(os.getenv('MIN_WITHDRAWAL', 100)),
                'max_amount': float(os.getenv('MAX_WITHDRAWAL', 5000)),
                'fee_percent': 2.0,
                'description': 'سحب سريع إلى محفظة تونز'
            },
            {
                'id': 'fawry',
                'name': 'فوري كاش',
                'icon': '🏦',
                'min_amount': float(os.getenv('MIN_WITHDRAWAL', 100)),
                'max_amount': float(os.getenv('MAX_WITHDRAWAL', 5000)),
                'fee_percent': 1.5,
                'description': 'سحب إلى محفظة فوري'
            }
        ]
    
    def calculate_fee(self, amount, payment_method):
        """Calculate withdrawal fee"""
        methods = self.get_payment_methods()
        method = next((m for m in methods if m['id'] == payment_method), None)
        
        if method:
            fee_percent = method['fee_percent']
            fee = amount * (fee_percent / 100)
            return round(fee, 2)
        
        return 0

class MockPaymentGateway(PaymentGateway):
    """Mock payment gateway for testing"""
    
    def process_withdrawal(self, amount, phone_number, payment_method, user_id):
        # Always successful for demo
        transaction_id = f"MOCK_TXN{user_id}_{int(datetime.now().timestamp())}"
        return True, transaction_id