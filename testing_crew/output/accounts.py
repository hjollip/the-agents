import sqlite3
import time
from typing import Optional, Dict, List

# Share price lookup (static for test)
def get_share_price(symbol: str) -> float:
    prices = {
        'AAPL': 175.0,
        'TSLA': 750.0,
        'GOOGL': 2650.0,
    }
    try:
        return prices[symbol.upper()]
    except KeyError:
        raise ValueError(f"Symbol '{symbol}' not supported.")


class Account:
    def __init__(self, username: str, db_path: str = "accounts.db"):
        self.db_path = db_path
        self.username = username
        self._init_db()

        user = self._execute(
            "SELECT username FROM users WHERE username = ?",
            (self.username,),
            fetchone=True
        )
        if not user:
            raise ValueError(f"Account '{self.username}' does not exist.")

    @classmethod
    def create_account(cls, username: str, initial_deposit: float, db_path: str = "accounts.db") -> "Account":
        # Init DB
        inst = cls.__new__(cls)
        inst.db_path = db_path
        inst.username = username
        inst._init_db()
        cur = inst._execute("SELECT username FROM users WHERE username = ?", (username,), fetchone=True)
        if cur:
            raise ValueError(f"Account '{username}' already exists.")
        if initial_deposit < 0:
            raise ValueError("Initial deposit must be non-negative.")
        inst._execute(
            "INSERT INTO users (username, balance, total_deposit) VALUES (?, ?, ?)",
            (username, initial_deposit, initial_deposit)
        )
        now = time.time()
        inst._execute(
            "INSERT INTO transactions (username, timestamp, type, symbol, quantity, price, amount, balance_after) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, now, "deposit", None, initial_deposit, None, initial_deposit, initial_deposit)
        )
        return cls(username, db_path)

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                balance REAL NOT NULL,
                total_deposit REAL NOT NULL
            )
        """)
        # holdings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                username TEXT,
                symbol TEXT,
                quantity INTEGER,
                PRIMARY KEY (username, symbol)
            )
        """)
        # transactions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp REAL NOT NULL,
                type TEXT NOT NULL,
                symbol TEXT,
                quantity REAL,
                price REAL,
                amount REAL,
                balance_after REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _execute(self, query: str, params: tuple = (), fetchone: bool = False, fetchall: bool = False):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        result = None
        if fetchone:
            result = cur.fetchone()
        elif fetchall:
            result = cur.fetchall()
        conn.commit()
        conn.close()
        return result

    # === Funds Management ===
    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        current = self._execute(
            "SELECT balance, total_deposit FROM users WHERE username = ?",
            (self.username,), fetchone=True
        )
        new_balance = current['balance'] + amount
        new_total_deposit = current['total_deposit'] + amount
        self._execute(
            "UPDATE users SET balance = ?, total_deposit = ? WHERE username = ?",
            (new_balance, new_total_deposit, self.username)
        )
        now = time.time()
        self._execute(
            "INSERT INTO transactions (username, timestamp, type, symbol, quantity, price, amount, balance_after) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (self.username, now, "deposit", None, amount, None, amount, new_balance)
        )

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        current = self._execute(
            "SELECT balance FROM users WHERE username = ?",
            (self.username,), fetchone=True
        )
        if current['balance'] < amount:
            raise ValueError("Insufficient funds for withdrawal.")
        new_balance = current['balance'] - amount
        self._execute(
            "UPDATE users SET balance = ? WHERE username = ?",
            (new_balance, self.username)
        )
        now = time.time()
        self._execute(
            "INSERT INTO transactions (username, timestamp, type, symbol, quantity, price, amount, balance_after) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (self.username, now, "withdraw", None, amount, None, -amount, new_balance)
        )

    # === Trading ===
    def buy(self, symbol: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Must buy a positive quantity.")
        price = get_share_price(symbol)
        total_cost = price * quantity
        user = self._execute(
            "SELECT balance FROM users WHERE username = ?",
            (self.username,), fetchone=True
        )
        if user['balance'] < total_cost:
            raise ValueError("Insufficient funds to buy.")
        # Update holdings
        hold = self._execute("SELECT quantity FROM holdings WHERE username = ? AND symbol = ?", (self.username, symbol), fetchone=True)
        if hold:
            new_q = hold['quantity'] + quantity
            self._execute("UPDATE holdings SET quantity = ? WHERE username = ? AND symbol = ?", (new_q, self.username, symbol))
        else:
            self._execute("INSERT INTO holdings (username, symbol, quantity) VALUES (?, ?, ?)", (self.username, symbol, quantity))
        # Update balance
        new_balance = user['balance'] - total_cost
        self._execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, self.username))
        # Transaction
        now = time.time()
        self._execute(
            "INSERT INTO transactions (username, timestamp, type, symbol, quantity, price, amount, balance_after) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (self.username, now, "buy", symbol, quantity, price, -total_cost, new_balance)
        )

    def sell(self, symbol: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Must sell a positive quantity.")
        price = get_share_price(symbol)
        hold = self._execute(
            "SELECT quantity FROM holdings WHERE username = ? AND symbol = ?",
            (self.username, symbol), fetchone=True
        )
        if not hold or hold['quantity'] < quantity:
            raise ValueError("Insufficient shares to sell.")
        # Update holdings
        new_q = hold['quantity'] - quantity
        if new_q > 0:
            self._execute("UPDATE holdings SET quantity = ? WHERE username = ? AND symbol = ?", (new_q, self.username, symbol))
        else:
            self._execute("DELETE FROM holdings WHERE username = ? AND symbol = ?", (self.username, symbol))
        proceeds = price * quantity
        user = self._execute(
            "SELECT balance FROM users WHERE username = ?",
            (self.username,), fetchone=True
        )
        new_balance = user['balance'] + proceeds
        self._execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, self.username))
        now = time.time()
        self._execute(
            "INSERT INTO transactions (username, timestamp, type, symbol, quantity, price, amount, balance_after) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (self.username, now, "sell", symbol, quantity, price, proceeds, new_balance)
        )

    # === Portfolio and Reporting ===
    def get_portfolio_value(self) -> float:
        user = self._execute("SELECT balance FROM users WHERE username = ?", (self.username,), fetchone=True)
        balance = user['balance']
        holdings = self._execute("SELECT symbol, quantity FROM holdings WHERE username = ?", (self.username,), fetchall=True)
        value = balance
        for row in holdings:
            value += row['quantity'] * get_share_price(row['symbol'])
        return value

    def get_profit_loss(self) -> float:
        user = self._execute("SELECT balance, total_deposit FROM users WHERE username = ?", (self.username,), fetchone=True)
        holdings = self._execute("SELECT symbol, quantity FROM holdings WHERE username = ?", (self.username,), fetchall=True)
        value = user['balance']
        for row in holdings:
            value += row['quantity'] * get_share_price(row['symbol'])
        return value - user['total_deposit']

    def get_profit_loss_at(self, timestamp: float) -> float:
        # Reconstruct user balance and holdings as of timestamp
        txs = self._execute(
            "SELECT * FROM transactions WHERE username = ? AND timestamp <= ? ORDER BY id ASC",
            (self.username, timestamp), fetchall=True
        )
        balance = 0.0
        total_deposit = 0.0
        holdings = {}
        for tx in txs:
            ttype = tx['type']
            if ttype == 'deposit':
                balance += float(tx['amount'])
                total_deposit += float(tx['amount'])
            elif ttype == 'withdraw':
                balance += float(tx['amount'])
            elif ttype == 'buy':
                symbol = tx['symbol']
                qty = int(tx['quantity'])
                price = float(tx['price'])
                balance -= qty * price
                holdings[symbol] = holdings.get(symbol, 0) + qty
            elif ttype == 'sell':
                symbol = tx['symbol']
                qty = int(tx['quantity'])
                price = float(tx['price'])
                balance += qty * price
                holdings[symbol] = holdings.get(symbol, 0) - qty
        # Remove zero or negative holdings
        for k in list(holdings.keys()):
            if holdings[k] <= 0:
                del holdings[k]
        value = balance
        for symbol, qty in holdings.items():
            value += qty * get_share_price(symbol)
        return value - total_deposit

    # === Holdings and Transactions ===
    def get_holdings(self) -> Dict[str, int]:
        holdings = self._execute("SELECT symbol, quantity FROM holdings WHERE username = ?", (self.username,), fetchall=True)
        return {row['symbol']: row['quantity'] for row in holdings}

    def get_holdings_at(self, timestamp: float) -> Dict[str, int]:
        txs = self._execute(
            "SELECT * FROM transactions WHERE username = ? AND timestamp <= ? ORDER BY id ASC",
            (self.username, timestamp), fetchall=True
        )
        holdings = {}
        for tx in txs:
            if tx['type'] == 'buy':
                symbol = tx['symbol']
                qty = int(tx['quantity'])
                holdings[symbol] = holdings.get(symbol, 0) + qty
            elif tx['type'] == 'sell':
                symbol = tx['symbol']
                qty = int(tx['quantity'])
                holdings[symbol] = holdings.get(symbol, 0) - qty
        # Remove zero or negative holdings
        for k in list(holdings.keys()):
            if holdings[k] <= 0:
                del holdings[k]
        return holdings

    def list_transactions(self, limit: int = 100, offset: int = 0) -> List[dict]:
        rows = self._execute(
            "SELECT * FROM transactions WHERE username = ? "
            "ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?",
            (self.username, limit, offset),
            fetchall=True
        )
        return [dict(row) for row in rows]