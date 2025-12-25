```markdown
# Design for `accounts.py` - Trading Simulation Account Management Module

## Overview

This module provides a SQL-backed account management system for a trading simulation platform. It defines the data models, logic, and interfaces required to allow for user account creation, fund management, trading of share assets, portfolio valuation, profit/loss calculations, transaction history, and enforcement of trading constraints. The external dependency is a price lookup function `get_share_price(symbol)`, for which a built-in test stub is also supplied.

---

## Classes and Functions

### 1. `Account` class

Represents a user's account. All account-related operations (funds, trades, holdings, reports) are exposed through instance methods. Methods automatically interact with the underlying SQLite database.

#### Constructor and Initialization

- **`__init__(self, username: str, db_path: str = "accounts.db")`**
  - Ensures the database and tables are initialized.
  - Loads the Account for `username` or raises if not found.

- **`@classmethod create_account(cls, username: str, initial_deposit: float, db_path: str = "accounts.db") -> "Account"`**
  - Creates a new user account with the given initial deposit.
  - Fails if the username already exists.

#### Database Utility Methods

- **`_init_db(self)`**
  - Creates required database schema if not present.
    - Tables: users, transactions, holdings

- **`_execute(self, query: str, params: tuple = (), fetchone: bool = False, fetchall: bool = False)`**
  - Helper to run DB queries with proper resource cleanup.

---

#### Fund Management

- **`deposit(self, amount: float) -> None`**
  - Increases available balance and records transaction.

- **`withdraw(self, amount: float) -> None`**
  - Decreases available balance (enforced: cannot go negative) and records transaction.

---

#### Trading (Buy/Sell Shares)

- **`buy(self, symbol: str, quantity: int) -> None`**
  - Checks sufficient balance.
  - Deducts required cash (at current price), updates holdings, records transaction.

- **`sell(self, symbol: str, quantity: int) -> None`**
  - Checks sufficient holdings.
  - Adds proceeds (at current price), updates holdings, records transaction.

---

#### Portfolio Valuation and Reporting

- **`get_portfolio_value(self) -> float`**
  - Sums the value of all holdings (at current prices) plus cash balance.

- **`get_profit_loss(self) -> float`**
  - Returns current value (portfolio + cash) minus total deposits.

- **`get_profit_loss_at(self, timestamp: float) -> float`**
  - Computes profit/loss as of a given timestamp (requires historical state replay).

---

#### Holdings and Transactions Reporting

- **`get_holdings(self) -> dict`**
  - Returns {symbol: quantity} for shares currently held.

- **`get_holdings_at(self, timestamp: float) -> dict`**
  - Returns holdings reconstructed as of a past time.

- **`list_transactions(self, limit: int = 100, offset: int = 0) -> list`**
  - Returns a list of transactions for this account in descending date order.

---

### 2. Transaction Recording

All methods above (deposit, withdraw, buy, sell) automatically construct and store a row in the `transactions` table that captures:
- timestamp
- transaction type
- symbol (if applicable)
- quantity
- price per share (for trade transactions)
- balance after transaction

---

### 3. Database Schema (created in `_init_db()`)

- **users**
  - username (primary key)
  - balance (float)
  - total_deposit (float)
- **holdings**
  - username
  - symbol
  - quantity
- **transactions**
  - id (primary key)
  - username
  - timestamp (float)
  - type (deposit, withdraw, buy, sell)
  - symbol (nullable)
  - quantity (nullable)
  - price (nullable)
  - amount (change in cash)
  - balance_after (balance after this transaction)

---

### 4. Price Lookup Helper

- **`get_share_price(symbol: str) -> float`**
  - Provided as a stub utility in the module—returns static prices for "AAPL", "TSLA", "GOOGL", raises for others.

---

## Example Method Signatures

```python
class Account:
    def __init__(self, username: str, db_path: str = "accounts.db"):
        ...

    @classmethod
    def create_account(cls, username: str, initial_deposit: float, db_path: str = "accounts.db") -> "Account":
        ...

    def deposit(self, amount: float) -> None:
        ...

    def withdraw(self, amount: float) -> None:
        ...

    def buy(self, symbol: str, quantity: int) -> None:
        ...

    def sell(self, symbol: str, quantity: int) -> None:
        ...

    def get_portfolio_value(self) -> float:
        ...

    def get_profit_loss(self) -> float:
        ...

    def get_profit_loss_at(self, timestamp: float) -> float:
        ...

    def get_holdings(self) -> dict:
        ...

    def get_holdings_at(self, timestamp: float) -> dict:
        ...

    def list_transactions(self, limit: int = 100, offset: int = 0) -> list:
        ...

def get_share_price(symbol: str) -> float:
    ...
```

---

## Trading & Account Rules (Enforced in Logic)

- Withdrawals must not cause balance to go negative.
- Buying more shares than affordable at current price is not allowed.
- Selling more shares than owned is not allowed.
- All transactions are journaled for replay/inspection.
- All portfolio and P&L reports reflect up-to-date market values by using `get_share_price`.

---

## Additional Notes

- The database is encapsulated and auto-managed; for test or UI purposes, everything can be run via `accounts.py` directly.
- All operations are synchronous and thread safety is not assumed.
- All API errors return exceptions with descriptive messages for UI/CLI handling.

---
```