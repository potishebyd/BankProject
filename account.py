import uuid
import enum

class AccountStatus(enum.Enum):
    active = 'ACTIVE'
    frozen = 'FROZEN'
    closed = 'CLOSED'

class Currency(enum.Enum):
    usd = "USD"
    rub = "RUB"
    eur = "EUR"
    kzt = "KZT"
    cny = "CNY"

class AccountFrozenError(Exception):
    pass

class AccountClosedError(Exception):
    pass

class InvalidOperationError(Exception):
    pass

class InsufficientError(Exception):
    pass


class AbstractAccount:
    def __init__(self, owner_data:str, balance:float = 0 , status:AccountStatus = AccountStatus.active, account_id:str = None):
        self._account_id = account_id
        self._owner_data = owner_data
        self._balance = balance
        self._status = status

    def deposit(self, amount):
        pass
    
    def withdraw(self, amount):
        pass

    def get_account_info(self):
        pass

class BankAccount(AbstractAccount):
    def __init__(self, owner_data : str, balance:float = 0.0 , status:AccountStatus = AccountStatus.active , account_id: str = None, currency : Currency = Currency.usd):
        
        if not isinstance(owner_data, str) or (owner_data == None):
            raise ValueError('Incorrect owner name')
        
        if not isinstance(balance, float):
            raise ValueError('Incorrect balance')

        if not isinstance(status, AccountStatus):
            raise ValueError('Incorrect status')
        
        if not isinstance(account_id, str) and account_id != None:
            raise ValueError('Incorrect account id')
        
        if not isinstance(currency, Currency):
            raise ValueError('Incorrect currency')
        

        if account_id:
            self._account_id = account_id
        else:
            self._account_id = uuid.uuid4()
        
        self._owner_data = owner_data
        self._balance = balance
        self._status = status
        self._currency = currency


    def check_status(self):
        if self._status == AccountStatus.frozen:
            raise AccountFrozenError('Account is frozen')
        if self._status == AccountStatus.closed:
            raise AccountClosedError('Account is closed')

    def check_amount(self, amount):
         if not isinstance(amount, float):
            raise InvalidOperationError('Incorrect amount (not float)')
         if amount < 0:
             raise InvalidOperationError('Incorrect amount (under zero)')
         

    def deposit(self, amount):
        self.check_status()
        self.check_amount(amount)
        self._balance += amount
    
    def withdraw(self, amount):
        self.check_status()
        self.check_amount(amount)
        if amount > self._balance:
            raise InsufficientError('Insufficient balance')
        self._balance -= amount

    def get_account_info(self):
        return {
            'account_id': self._account_id,
            'owner_data': self._owner_data,
            'balance': self._balance,
            'status': self._status,
            'currency': self._currency
        }
    
    def __str__(self):
        return f'({self._account_id}, {self._owner_data}, {self._status}, {self._balance}, {self._currency})'
        

# Создание авктовного и замороженного счета
active_check = BankAccount('Sigma',10.2, AccountStatus.active)
frozen_check = BankAccount('Lox', 4.2, AccountStatus.frozen)

# Операция над замороженным счетом
try:
    frozen_check.deposit(2.5)
except AccountFrozenError as error:
    print("Error:", error)

try:
    frozen_check.withdraw(2.5)
except AccountFrozenError as error:
    print("Error:", error)


# Валидное пополнение и снятие 

active_check.deposit(5.5)
print(active_check)
active_check.withdraw(3.4)
print(active_check)