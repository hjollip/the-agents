# Utility function to get mock share prices
def get_share_price(symbol: str) -> float:
    prices = {
        'AAPL': 150.0,
        'TSLA': 700.0,
        'GOOGL': 2800.0
    }
    return prices.get(symbol, 0.0)

class Account:
    def __init__(self, account_id: str, initial_deposit: float) -> None:
        self.account_id = account_id
        self.initial_deposit = initial_deposit
        self.balance = initial_deposit
        self.holdings = {}
        self.transactions = []
        self.transactions.append({'type': 'initial_deposit', 'amount': initial_deposit})

    def deposit_funds(self, amount: float) -> None:
        self.balance += amount
        self.transactions.append({'type': 'deposit', 'amount': amount})

    def withdraw_funds(self, amount: float) -> None:
        if amount > self.balance:
            raise Exception("Insufficient funds for withdrawal.")
        self.balance -= amount
        self.transactions.append({'type': 'withdrawal', 'amount': amount})

    def buy_shares(self, symbol: str, quantity: int) -> None:
        price_per_share = get_share_price(symbol)
        total_cost = price_per_share * quantity
        if total_cost > self.balance:
            raise Exception("Insufficient funds to buy shares.")
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append({'type': 'buy', 'symbol': symbol, 'quantity': quantity, 'price': price_per_share})

    def sell_shares(self, symbol: str, quantity: int) -> None:
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise Exception("Not enough shares to sell.")
        price_per_share = get_share_price(symbol)
        total_income = price_per_share * quantity
        self.balance += total_income
        self.holdings[symbol] -= quantity
        self.transactions.append({'type': 'sell', 'symbol': symbol, 'quantity': quantity, 'price': price_per_share})
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

    def calculate_portfolio_value(self) -> float:
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def calculate_profit_loss(self) -> float:
        current_value = self.calculate_portfolio_value()
        return current_value - self.initial_deposit

    def get_holdings(self) -> dict:
        return self.holdings.copy()

    def get_profit_loss_report(self) -> dict:
        profit_loss = self.calculate_profit_loss()
        return {
            'initial_deposit': self.initial_deposit,
            'current_balance': self.balance,
            'current_portfolio_value': self.calculate_portfolio_value(),
            'profit_loss': profit_loss
        }

    def list_transactions(self) -> list:
        return self.transactions.copy()