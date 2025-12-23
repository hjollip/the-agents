import unittest
from accounts import Account, get_share_price

class TestAccount(unittest.TestCase):
    def test_initial_deposit(self):
        account = Account('001', 1000.0)
        self.assertEqual(account.balance, 1000.0)
        self.assertEqual(account.list_transactions(), [{'type': 'initial_deposit', 'amount': 1000.0}])

    def test_deposit_funds(self):
        account = Account('002', 500.0)
        account.deposit_funds(200.0)
        self.assertEqual(account.balance, 700.0)
        self.assertEqual(account.list_transactions()[1], {'type': 'deposit', 'amount': 200.0})

    def test_withdraw_funds(self):
        account = Account('003', 1000.0)
        account.withdraw_funds(300.0)
        self.assertEqual(account.balance, 700.0)
        self.assertEqual(account.list_transactions()[1], {'type': 'withdrawal', 'amount': 300.0})

    def test_withdraw_funds_exceeding_balance(self):
        account = Account('004', 100.0)
        with self.assertRaises(Exception) as context:
            account.withdraw_funds(200.0)
        self.assertEqual(str(context.exception), 'Insufficient funds for withdrawal.')

    def test_buy_shares(self):
        account = Account('005', 5000.0)
        account.buy_shares('AAPL', 10)
        self.assertEqual(account.holdings['AAPL'], 10)
        self.assertAlmostEqual(account.balance, 3500.0, delta=0.01)
        self.assertEqual(account.list_transactions()[1], {'type': 'buy', 'symbol': 'AAPL', 'quantity': 10, 'price': 150.0})

    def test_buy_shares_exceeding_balance(self):
        account = Account('006', 500.0)
        with self.assertRaises(Exception) as context:
            account.buy_shares('AAPL', 10)
        self.assertEqual(str(context.exception), 'Insufficient funds to buy shares.')

    def test_sell_shares(self):
        account = Account('007', 5000.0)
        account.buy_shares('AAPL', 10)
        account.sell_shares('AAPL', 5)
        self.assertEqual(account.holdings['AAPL'], 5)
        self.assertAlmostEqual(account.balance, 4250.0, delta=0.01)
        self.assertEqual(account.list_transactions()[2], {'type': 'sell', 'symbol': 'AAPL', 'quantity': 5, 'price': 150.0})

    def test_sell_shares_not_owned(self):
        account = Account('008', 500.0)
        with self.assertRaises(Exception) as context:
            account.sell_shares('AAPL', 10)
        self.assertEqual(str(context.exception), 'Not enough shares to sell.')

    def test_calculate_portfolio_value(self):
        account = Account('009', 1000.0)
        account.buy_shares('TSLA', 2)
        account.buy_shares('AAPL', 2)
        portfolio_value = account.calculate_portfolio_value()
        expected_value = 2 * get_share_price('TSLA') + 2 * get_share_price('AAPL') + account.balance
        self.assertAlmostEqual(portfolio_value, expected_value, delta=0.01)

    def test_calculate_profit_loss(self):
        account = Account('010', 2000.0)
        account.buy_shares('GOOGL', 1)
        profit_loss = account.calculate_profit_loss()
        expected_current_value = get_share_price('GOOGL') + account.balance
        expected_profit_loss = expected_current_value - account.initial_deposit
        self.assertAlmostEqual(profit_loss, expected_profit_loss, delta=0.01)

    def test_get_profit_loss_report(self):
        account = Account('011', 1500.0)
        account.buy_shares('TSLA', 1)
        report = account.get_profit_loss_report()
        self.assertAlmostEqual(report['profit_loss'], account.calculate_profit_loss(), delta=0.01)

if __name__ == '__main__':
    unittest.main()