import gradio as gr
import time
from datetime import datetime
from accounts import Account

DB_PATH = "accounts.db"  # Same as in backend
USERNAME = "demo_user"   # Single-user demo; fixed username


def ensure_account_exists():
    try:
        acct = Account(USERNAME, db_path=DB_PATH)
        return acct
    except ValueError:
        # By default, create account with 0 deposit -- but will prompt for deposit on UI
        return None


def create_account_ui(initial_deposit):
    try:
        acct = Account.create_account(USERNAME, initial_deposit, db_path=DB_PATH)
        return "Account created with deposit ${:.2f}".format(initial_deposit)
    except Exception as e:
        return f"Error: {e}"


def deposit_ui(amount):
    try:
        acct = ensure_account_exists()
        if acct is None:
            return "Error: Account does not exist. Please create one."
        acct.deposit(float(amount))
        return "Deposited ${:.2f}".format(float(amount))
    except Exception as e:
        return f"Error: {e}"


def withdraw_ui(amount):
    try:
        acct = ensure_account_exists()
        if acct is None:
            return "Error: Account does not exist. Please create one."
        acct.withdraw(float(amount))
        return "Withdrew ${:.2f}".format(float(amount))
    except Exception as e:
        return f"Error: {e}"


def buy_ui(symbol, quantity):
    try:
        acct = ensure_account_exists()
        if acct is None:
            return "Error: Account does not exist. Please create one."
        symbol = symbol.strip().upper()
        acct.buy(symbol, int(quantity))
        return f"Bought {quantity} shares of {symbol}."
    except Exception as e:
        return f"Error: {e}"


def sell_ui(symbol, quantity):
    try:
        acct = ensure_account_exists()
        if acct is None:
            return "Error: Account does not exist. Please create one."
        symbol = symbol.strip().upper()
        acct.sell(symbol, int(quantity))
        return f"Sold {quantity} shares of {symbol}."
    except Exception as e:
        return f"Error: {e}"


def portfolio_status_ui():
    try:
        acct = ensure_account_exists()
        if acct is None:
            return "Error: Account does not exist. Please create one.", "", ""
        value = acct.get_portfolio_value()
        p_l = acct.get_profit_loss()
        holdings = acct.get_holdings()
        text = "Portfolio Value: ${:.2f}\nProfit/Loss: ${:.2f}\n".format(value, p_l)
        if holdings:
            text += "Holdings:\n"
            for symbol, qty in holdings.items():
                text += f"  {symbol}: {qty}\n"
        else:
            text += "No stock holdings."
        return text, value, p_l
    except Exception as e:
        return f"Error: {e}", "", ""


def holdings_at_ui(date_str):
    try:
        acct = ensure_account_exists()
        if acct is None:
            return "Error: Account does not exist. Please create one."
        # Accepts "YYYY-MM-DD HH:MM:SS"
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return "Invalid date/time format. Use 'YYYY-MM-DD HH:MM:SS'"
        timestamp = dt.timestamp()
        holdings = acct.get_holdings_at(timestamp)
        if not holdings:
            return "No holdings at that time."
        return "\n".join([f"{k}: {v}" for k, v in holdings.items()])
    except Exception as e:
        return f"Error: {e}"


def profit_loss_at_ui(date_str):
    try:
        acct = ensure_account_exists()
        if acct is None:
            return "Error: Account does not exist. Please create one."
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return "Invalid date/time format. Use 'YYYY-MM-DD HH:MM:SS'"
        timestamp = dt.timestamp()
        pl = acct.get_profit_loss_at(timestamp)
        return f"Profit/Loss as of {date_str}: ${pl:.2f}"
    except Exception as e:
        return f"Error: {e}"


def transactions_ui():
    try:
        acct = ensure_account_exists()
        if acct is None:
            return [["Please create an account first."]]
        txs = acct.list_transactions(limit=25, offset=0)
        if not txs:
            return [["No transactions yet."]]
        table = []
        header = ["Time", "Type", "Symbol", "Qty", "Price", "Amount", "Balance"]
        table.append(header)
        for tx in txs:
            dt = datetime.fromtimestamp(tx['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            ttype = tx['type']
            symbol = tx['symbol'] or ""
            qty = tx['quantity'] if tx['quantity'] is not None else ""
            price = "${:.2f}".format(tx['price']) if tx['price'] is not None else ""
            amount = "${:.2f}".format(tx['amount']) if tx['amount'] is not None else ""
            balance = "${:.2f}".format(tx['balance_after']) if tx['balance_after'] is not None else ""
            row = [dt, ttype, symbol, qty, price, amount, balance]
            table.append(row)
        return table
    except Exception as e:
        return [[f"Error: {e}"]]


with gr.Blocks(title="Trading Account Demo") as demo:
    gr.Markdown("# Trading Account Demo (Prototype)")
    with gr.Tab("Create Account"):
        gr.Markdown("Create account demo_user (single-user demo).")
        init_deposit = gr.Number(label="Initial Deposit (USD)", value=1000.0)
        create_btn = gr.Button("Create Account")
        create_out = gr.Textbox(label="Result")
        create_btn.click(create_account_ui, [init_deposit], create_out)
    with gr.Tab("Deposits / Withdrawals"):
        gr.Markdown("Deposit or withdraw funds.")
        with gr.Row():
            dep_amt = gr.Number(label="Deposit Amount (USD)", value=100.0)
            dep_btn = gr.Button("Deposit")
            dep_out = gr.Textbox(label="Result")
            dep_btn.click(deposit_ui, [dep_amt], dep_out)
        with gr.Row():
            wdr_amt = gr.Number(label="Withdraw Amount (USD)", value=100.0)
            wdr_btn = gr.Button("Withdraw")
            wdr_out = gr.Textbox(label="Result")
            wdr_btn.click(withdraw_ui, [wdr_amt], wdr_out)
    with gr.Tab("Trade Shares"):
        gr.Markdown("Buy or sell demo stocks ('AAPL', 'TSLA', 'GOOGL').")
        with gr.Row():
            buy_symbol = gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], label="Symbol", value="AAPL")
            buy_qty = gr.Number(label="Quantity", value=1, precision=0)
            buy_btn = gr.Button("Buy")
            buy_out = gr.Textbox(label="Result")
            buy_btn.click(buy_ui, [buy_symbol, buy_qty], buy_out)
        with gr.Row():
            sell_symbol = gr.Dropdown(choices=["AAPL", "TSLA", "GOOGL"], label="Symbol", value="AAPL")
            sell_qty = gr.Number(label="Quantity", value=1, precision=0)
            sell_btn = gr.Button("Sell")
            sell_out = gr.Textbox(label="Result")
            sell_btn.click(sell_ui, [sell_symbol, sell_qty], sell_out)
    with gr.Tab("Portfolio & Holdings"):
        gr.Markdown("See value, P/L, and holdings.")
        port_btn = gr.Button("Refresh Portfolio")
        port_text = gr.Textbox(label="Portfolio Status", lines=5)
        port_val = gr.Number(label="Portfolio Value", interactive=False)
        port_pl = gr.Number(label="Profit/Loss", interactive=False)
        port_btn.click(portfolio_status_ui, inputs=None, outputs=[port_text, port_val, port_pl])
        gr.Markdown("Show holdings as of... (format: YYYY-MM-DD HH:MM:SS)")
        hold_time = gr.Textbox(label="Timestamp", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        hold_btn = gr.Button("View Holdings at Time")
        hold_out = gr.Textbox(label="Holdings at Time", lines=3)
        hold_btn.click(holdings_at_ui, [hold_time], hold_out)
        gr.Markdown("Show profit/loss as of... (format: YYYY-MM-DD HH:MM:SS)")
        pl_time = gr.Textbox(label="Timestamp", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        pl_btn = gr.Button("View P/L at Time")
        pl_out = gr.Textbox(label="Profit/Loss at Time", lines=1)
        pl_btn.click(profit_loss_at_ui, [pl_time], pl_out)
    with gr.Tab("Transactions Log"):
        gr.Markdown("Recent transactions.")
        tx_btn = gr.Button("Refresh Transactions")
        tx_table = gr.Dataframe(label="Transactions", headers=None, interactive=False)
        tx_btn.click(transactions_ui, inputs=None, outputs=tx_table)

if __name__ == "__main__":
    demo.launch()