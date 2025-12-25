import pytest
import os
import tempfile
import time

from accounts import Account, get_share_price

@pytest.fixture
def temp_db():
    """Create and destroy a temporary sqlite DB file for each test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_get_share_price_valid():
    assert get_share_price('AAPL') == 175.0
    assert get_share_price('tsla') == 750.0
    assert get_share_price('Googl') == 2650.0

def test_get_share_price_invalid():
    with pytest.raises(ValueError):
        get_share_price('MSFT')

def test_create_account_and_initial_balance(temp_db):
    acct = Account.create_account("alice", 1000.0, db_path=temp_db)
    # Should raise error if already exists
    with pytest.raises(ValueError):
        Account.create_account("alice", 500, db_path=temp_db)
    # Missing account raises error
    with pytest.raises(ValueError):
        Account("bob", db_path=temp_db)
    # Negative deposit
    with pytest.raises(ValueError):
        Account.create_account("bob", -10, db_path=temp_db)
    # Initial deposit reflected in balance
    alice = Account("alice", db_path=temp_db)
    assert alice._execute("SELECT balance FROM users WHERE username = ?", ("alice",), fetchone=True)["balance"] == 1000.0

def test_deposit(temp_db):
    acct = Account.create_account("alice", 100.0, db_path=temp_db)
    acct.deposit(500.0)
    rec = acct._execute("SELECT balance, total_deposit FROM users WHERE username = ?", ("alice",), fetchone=True)
    assert rec["balance"] == 600.0
    assert rec["total_deposit"] == 600.0
    # Zero/negative deposit rejected
    with pytest.raises(ValueError):
        acct.deposit(0)
    with pytest.raises(ValueError):
        acct.deposit(-1)

def test_withdraw(temp_db):
    acct = Account.create_account("alice", 1000.0, db_path=temp_db)
    acct.withdraw(300.0)
    rec = acct._execute("SELECT balance FROM users WHERE username = ?", ("alice",), fetchone=True)
    assert rec["balance"] == 700.0
    # Excess withdrawal
    with pytest.raises(ValueError):
        acct.withdraw(1000)
    with pytest.raises(ValueError):
        acct.withdraw(0)
    with pytest.raises(ValueError):
        acct.withdraw(-5)

def test_buy_basic(temp_db):
    acct = Account.create_account("alice", 3000.0, db_path=temp_db)
    before = acct.get_holdings()
    assert before == {}
    acct.buy('AAPL', 5)  # 875 cost
    rec = acct._execute("SELECT balance FROM users WHERE username = ?", ("alice",), fetchone=True)
    assert pytest.approx(rec["balance"], 0.01) == 3000 - 5*175.0
    # Holdings updated
    holds = acct.get_holdings()
    assert holds == {'AAPL': 5}
    # Second buy (increase shares)
    acct.buy('AAPL', 2)
    holds2 = acct.get_holdings()
    assert holds2['AAPL'] == 7

def test_buy_insufficient_funds(temp_db):
    acct = Account.create_account("alice", 100.0, db_path=temp_db)
    with pytest.raises(ValueError):
        acct.buy('GOOGL', 1)
    with pytest.raises(ValueError):
        acct.buy('AAPL', 0)
    with pytest.raises(ValueError):
        acct.buy('TSLA', -1)

def test_sell_basic(temp_db):
    acct = Account.create_account("alice", 5000.0, db_path=temp_db)
    acct.buy('AAPL', 10)
    acct.sell('AAPL', 4)
    holds = acct.get_holdings()
    assert holds['AAPL'] == 6
    # Balance increases correctly
    rec = acct._execute("SELECT balance FROM users WHERE username = ?", ("alice",), fetchone=True)
    assert pytest.approx(rec["balance"], 0.01) == 5000.0 - 10*175.0 + 4*175.0

def test_sell_entire_holding(temp_db):
    acct = Account.create_account("alice", 2000.0, db_path=temp_db)
    acct.buy('TSLA', 2)
    assert acct.get_holdings()['TSLA'] == 2
    acct.sell('TSLA', 2)
    # Holdings should remove symbol key when shares are zeroed out
    holds = acct.get_holdings()
    assert 'TSLA' not in holds

def test_sell_too_many_shares(temp_db):
    acct = Account.create_account("alice", 3000.0, db_path=temp_db)
    acct.buy('AAPL', 1)
    with pytest.raises(ValueError):
        acct.sell('AAPL', 2)
    with pytest.raises(ValueError):
        acct.sell('AAPL', 0)
    with pytest.raises(ValueError):
        acct.sell('AAPL', -2)
    with pytest.raises(ValueError):
        acct.sell('TSLA', 1)

def test_get_portfolio_value_and_profit_loss(temp_db):
    acct = Account.create_account("alice", 900.0, db_path=temp_db)
    # No holdings, only cash
    assert pytest.approx(acct.get_portfolio_value(), 0.01) == 900.0
    assert pytest.approx(acct.get_profit_loss(), 0.01) == 0.0
    acct.buy('AAPL', 2)  # 350 cost
    port = acct.get_portfolio_value()
    assert pytest.approx(port, 0.01) == (900.0 - 350.0) + 2*175.0  # Should be 900
    # Add cash by deposit, simulates more movement
    acct.deposit(100.0)
    assert pytest.approx(acct.get_profit_loss(), 0.01) == acct.get_portfolio_value() - 1000.0

def test_get_profit_loss_at(temp_db):
    acct = Account.create_account("bob", 1000.0, db_path=temp_db)
    acct.deposit(1000.0)
    t1 = time.time()
    time.sleep(0.01)
    acct.buy('TSLA', 2)
    t2 = time.time()
    time.sleep(0.01)
    acct.deposit(250.0)
    t3 = time.time()
    # Profit loss just after t1: 2000 cash, no shares, total_deposit 2000
    at_t1 = acct.get_profit_loss_at(t1)
    assert pytest.approx(at_t1, 0.01) == 0.0
    # After t2 (buy TSLA): Should reflect 2 TSLA shares + leftover cash, minus total_deposit
    tsla_price = get_share_price('TSLA')
    spent = tsla_price*2
    portval = (2000 - spent) + 2*tsla_price
    pl = portval - 2000
    at_t2 = acct.get_profit_loss_at(t2)
    assert pytest.approx(at_t2, 0.01) == pl
    # After deposit at t3
    at_t3 = acct.get_profit_loss_at(t3)
    nowval = (2000 - spent + 250) + 2*tsla_price
    totaldep = 2250.0
    assert pytest.approx(at_t3, 0.01) == nowval - totaldep

def test_get_holdings_and_holdings_at(temp_db):
    acct = Account.create_account("alice", 1500.0, db_path=temp_db)
    acct.buy('AAPL', 1)
    t1 = time.time()
    time.sleep(0.01)
    acct.buy('TSLA', 2)
    t2 = time.time()
    time.sleep(0.01)
    acct.sell('TSLA', 1)
    t3 = time.time()
    # Current holdings
    h_now = acct.get_holdings()
    assert h_now == {'AAPL': 1, 'TSLA': 1}
    # Just after first buy
    h1 = acct.get_holdings_at(t1)
    assert h1 == {'AAPL': 1}
    # After second buy
    h2 = acct.get_holdings_at(t2)
    assert h2 == {'AAPL': 1, 'TSLA': 2}
    # After sell
    h3 = acct.get_holdings_at(t3)
    assert h3 == {'AAPL': 1, 'TSLA': 1}

def test_list_transactions(temp_db):
    acct = Account.create_account("alice", 999.0, db_path=temp_db)
    acct.deposit(1.0)
    acct.withdraw(100.0)
    acct.buy('AAPL', 2)
    acct.sell('AAPL', 1)
    txs = acct.list_transactions()
    # By default returns all, most recent first
    assert len(txs) == 5
    types = [tx['type'] for tx in txs]
    # Most recent to oldest
    assert types == ['sell', 'buy', 'withdraw', 'deposit', 'deposit']
    # Limit
    first_2 = acct.list_transactions(limit=2)
    assert len(first_2) == 2
    # Offset
    offs = acct.list_transactions(limit=2, offset=2)
    assert [tx['type'] for tx in offs] == ['withdraw', 'deposit']

def test_multiple_accounts_isolation(temp_db):
    a1 = Account.create_account("a1", 500.0, db_path=temp_db)
    a2 = Account.create_account("a2", 1000.0, db_path=temp_db)
    a1.buy('AAPL', 1)
    a2.buy('TSLA', 1)
    assert a1.get_holdings() == {'AAPL': 1}
    assert a2.get_holdings() == {'TSLA': 1}
    # Buying more in one does not affect the other
    a2.buy('AAPL', 2)
    assert a1.get_holdings() == {'AAPL': 1}
    assert a2.get_holdings()['AAPL'] == 2

# End of tests