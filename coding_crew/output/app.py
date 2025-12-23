import gradio as gr
from accounts import Account

def create_account(initial_deposit):
    global user_account
    user_account = Account(account_id="user_001", initial_deposit=initial_deposit)
    return "Account created with initial deposit of $%.2f" % initial_deposit

def deposit_funds(amount):
    try:
        user_account.deposit_funds(amount)
        return "Deposited $%.2f, new balance $%.2f" % (amount, user_account.balance)
    except Exception as e:
        return str(e)

def withdraw_funds(amount):
    try:
        user_account.withdraw_funds(amount)
        return "Withdrew $%.2f, new balance $%.2f" % (amount, user_account.balance)
    except Exception as e:
        return str(e)

def buy_shares(symbol, quantity):
    try:
        user_account.buy_shares(symbol, quantity)
        return "Bought %d shares of %s" % (quantity, symbol)
    except Exception as e:
        return str(e)

def sell_shares(symbol, quantity):
    try:
        user_account.sell_shares(symbol, quantity)
        return "Sold %d shares of %s" % (quantity, symbol)
    except Exception as e:
        return str(e)

def portfolio_value():
    return user_account.calculate_portfolio_value()

def profit_loss_report():
    report = user_account.get_profit_loss_report()
    return "Initial deposit: $%.2f\nCurrent balance: $%.2f\nCurrent portfolio value: $%.2f\nProfit/Loss: $%.2f" % (
        report['initial_deposit'], report['current_balance'], report['current_portfolio_value'], report['profit_loss']
    )

def list_holdings():
    holdings = user_account.get_holdings()
    return "\n".join([f"{symbol}: {quantity} shares" for symbol, quantity in holdings.items()])

def list_transactions():
    transactions = user_account.list_transactions()
    return "\n".join(
        [f"{t['type']} - Amount: ${t.get('amount', 'N/A')} Symbol: {t.get('symbol', 'N/A')} Quantity: {t.get('quantity', 'N/A')} Price: ${t.get('price', 'N/A')}" 
         for t in transactions]
    )

def create_ui():
    with gr.Blocks() as demo:
        gr.Markdown("## Simple Trading Simulation Platform")

        with gr.TabItem("Create Account"):
            initial_deposit = gr.Number(label="Initial Deposit")
            create_btn = gr.Button("Create Account")
            create_output = gr.Textbox(label="Status")
            create_btn.click(fn=create_account, inputs=initial_deposit, outputs=create_output)

        with gr.TabItem("Deposit Funds"):
            deposit_amount = gr.Number(label="Deposit Amount")
            deposit_btn = gr.Button("Deposit")
            deposit_output = gr.Textbox(label="Status")
            deposit_btn.click(fn=deposit_funds, inputs=deposit_amount, outputs=deposit_output)

        with gr.TabItem("Withdraw Funds"):
            withdraw_amount = gr.Number(label="Withdraw Amount")
            withdraw_btn = gr.Button("Withdraw")
            withdraw_output = gr.Textbox(label="Status")
            withdraw_btn.click(fn=withdraw_funds, inputs=withdraw_amount, outputs=withdraw_output)

        with gr.TabItem("Trade Shares"):
            symbol = gr.Textbox(label="Stock Symbol (e.g., AAPL, TSLA, GOOGL)")
            quantity = gr.Number(label="Quantity")
            buy_btn = gr.Button("Buy Shares")
            buy_output = gr.Textbox(label="Status")
            buy_btn.click(fn=buy_shares, inputs=[symbol, quantity], outputs=buy_output)

            sell_btn = gr.Button("Sell Shares")
            sell_output = gr.Textbox(label="Status")
            sell_btn.click(fn=sell_shares, inputs=[symbol, quantity], outputs=sell_output)

        with gr.TabItem("Portfolio Info"):
            portfolio_btn = gr.Button("Get Portfolio Value")
            portfolio_output = gr.Number(label="Portfolio Value")
            portfolio_btn.click(fn=portfolio_value, inputs=None, outputs=portfolio_output)

            holdings_btn = gr.Button("Get Holdings")
            holdings_output = gr.Textbox(label="Current Holdings")
            holdings_btn.click(fn=list_holdings, inputs=None, outputs=holdings_output)

            profit_loss_btn = gr.Button("Get Profit/Loss Report")
            profit_loss_output = gr.Textbox(label="Profit/Loss Report", lines=5)
            profit_loss_btn.click(fn=profit_loss_report, inputs=None, outputs=profit_loss_output)

        with gr.TabItem("Transaction History"):
            transactions_btn = gr.Button("List Transactions")
            transactions_output = gr.Textbox(label="Transaction History", lines=10)
            transactions_btn.click(fn=list_transactions, inputs=None, outputs=transactions_output)

    return demo

user_account = None
ui = create_ui()
ui.launch()