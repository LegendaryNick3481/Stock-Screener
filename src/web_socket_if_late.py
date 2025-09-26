import tkinter as tk
from fyers_apiv3.FyersWebsocket import data_ws
import pandas as pd
import credentials as crs
#import screener
import fetch_open
from datetime import datetime, time as dtime
import file_paths as fp


class FyersLiveTracker:
    def __init__(self):
        self.invalid_symbols = []
        self.ltp_data = {}
        self.change_data = {}
        self.ticker_widgets = {}
        self.positions = {}
        self.trade_log = {}
        self.net_pnls = {}
        self.market_closed = False
        self.openPrices = {}
        self.open_fetched = False
        self.capital_per_stock = 500 * 5

        self.ticker_df = pd.read_csv(fp.ticker_data_file)
        self.tickerList = self.ticker_df['Symbol'].tolist()

        with open(fp.access_token_file) as file:
            self.access_token = file.read().strip()

        self.setup_gui()
        self.setup_fyers()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Fyers Live LTP")
        self.root.geometry("700x600")
        self.root.configure(bg='black')

        title = tk.Label(self.root, text="Live LTP Updates", bg='black', fg='white', font=("Arial", 16, "bold"))
        title.pack(pady=5)

        self.net_pnl_lbl = tk.Label(self.root, text="Net PnL: ₹0.00", bg='black', fg='cyan', font=("Arial", 12, "bold"))
        self.net_pnl_lbl.pack()

        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg='black', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='black')

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.create_header()
        self.create_rows()
        self.root.after(1000, self.update_gui)
        self.root.after(60000, self.check_exit_time)
        self.root.after(0, self.fetch_open_prices_if_market_open)

    def fetch_open_prices_if_market_open(self):
        if datetime.now().time() >= dtime(9, 16, 30) and not self.open_fetched:
            self.openPrices = fetch_open.fetch(self.tickerList)
            print(self.openPrices)
            self.open_fetched = True
            print("[INFO] Fetched open prices")

            for symbol in self.tickerList:
                ltp = self.ltp_data.get(symbol)
                open_price = self.openPrices.get(symbol)
                if ltp and open_price and symbol not in self.positions:
                    target_buy_price = open_price * 1.03
                    if ltp >= target_buy_price:
                        qty = max(1, int(self.capital_per_stock / target_buy_price))
                        buy_price = target_buy_price * 1.001
                        self.positions[symbol] = {'buy_price': buy_price, 'buy_time': datetime.now(), 'qty': qty}
                        print(
                            f"[ASSUMED 3% BUY] {symbol} at {buy_price:.2f} | Qty: {qty} | Current Change: {((ltp - open_price) / open_price) * 100:.2f}%")
        else:
            self.root.after(1000, self.fetch_open_prices_if_market_open)

    def create_header(self):
        header = tk.Frame(self.scrollable_frame, bg='black')
        header.pack(fill=tk.X, padx=10, pady=5)

        headers = ["Ticker", "LTP", "% Change", "Live PnL", "Net PnL"]
        for col, text in enumerate(headers):
            tk.Label(
                header, text=text, fg='white', bg='black',
                width=12, anchor='e', font=('Consolas', 12, 'bold')
            ).grid(row=0, column=col, padx=5)

    def create_rows(self):
        for i, ticker in enumerate(self.tickerList):
            row = tk.Frame(self.scrollable_frame, bg='black')

            tk.Label(row, text=ticker.split(":")[-1], fg='white', bg='black', width=12, anchor='w',
                     font=('Consolas', 12)).grid(row=0, column=0, padx=5)

            ltp_lbl = tk.Label(row, text="--", fg='lime', bg='black', width=12, anchor='e',
                               font=('Consolas', 12, 'bold'))
            ltp_lbl.grid(row=0, column=1, padx=5)

            change_lbl = tk.Label(row, text="--", fg='yellow', bg='black', width=12, anchor='e', font=('Consolas', 12))
            change_lbl.grid(row=0, column=2, padx=5)

            live_pnl_lbl = tk.Label(row, text="--", fg='white', bg='black', width=12, anchor='e', font=('Consolas', 12))
            live_pnl_lbl.grid(row=0, column=3, padx=5)

            net_pnl_lbl = tk.Label(row, text="₹0.00", fg='cyan', bg='black', width=12, anchor='e',
                                   font=('Consolas', 12))
            net_pnl_lbl.grid(row=0, column=4, padx=5)

            self.ticker_widgets[ticker] = (row, ltp_lbl, change_lbl, live_pnl_lbl, net_pnl_lbl)

    def sort_rows_by_change(self):
        """Sort rows by percentage change in descending order"""
        # Get all symbols that have change data
        symbols_with_change = [(symbol, self.change_data.get(symbol, -999)) for symbol in self.tickerList if
                               symbol in self.ticker_widgets]

        # Sort by change percentage in descending order
        symbols_with_change.sort(key=lambda x: x[1], reverse=True)

        # Repack rows in sorted order
        for i, (symbol, change) in enumerate(symbols_with_change):
            if symbol in self.ticker_widgets:
                row, *_ = self.ticker_widgets[symbol]
                row.pack_forget()  # Remove from current position
                row.pack(fill=tk.X, padx=10, pady=2)  # Repack in new position

    def update_gui(self):
        if self.market_closed or not self.open_fetched:
            self.root.after(1000, self.update_gui)
            return

        net_pnl_total = 0
        for symbol, ltp in self.ltp_data.items():
            if symbol not in self.ticker_widgets:
                continue
            _, ltp_lbl, change_lbl, live_pnl_lbl, net_pnl_lbl = self.ticker_widgets[symbol]
            ltp_lbl.config(text=f"{ltp:.2f}")

            open_price = self.openPrices.get(symbol)
            if open_price:
                change = ((ltp - open_price) / open_price) * 100
                self.change_data[symbol] = change
                color = 'green' if change >= 0 else 'red'
                change_lbl.config(text=f"{change:+.2f}%", fg=color)

                target_buy_price = open_price * 1.03
                if ltp >= target_buy_price and symbol not in self.positions:
                    qty = max(1, int(self.capital_per_stock / target_buy_price))
                    buy_price = target_buy_price * 1.001
                    self.positions[symbol] = {'buy_price': buy_price, 'buy_time': datetime.now(), 'qty': qty}
                    print(f"[REALTIME 3% BUY] {symbol} at {buy_price:.2f} | Qty: {qty} | Change: {change:.2f}%")

                if symbol in self.positions:
                    buy = self.positions[symbol]
                    qty = buy['qty']
                    buy_price = buy['buy_price']
                    sell_price = ltp * 0.999

                    gross = (sell_price - buy_price) * qty
                    turnover = (buy_price + sell_price) * qty
                    buy_brokerage = min(0.0003 * buy_price * qty, 20)
                    sell_brokerage = min(0.0003 * sell_price * qty, 20)
                    charges = buy_brokerage + sell_brokerage + (turnover * 0.0003)
                    pnl = gross - charges

                    pnl_color = 'green' if pnl >= 0 else 'red'
                    live_pnl_lbl.config(text=f"{pnl:+.2f}", fg=pnl_color)
                    net_pnl_total += pnl

                    if sell_price <= buy_price * 0.995:
                        self.trade_log[symbol] = {'buy_price': buy_price, 'sell_price': sell_price, 'pnl': pnl,
                                                  'qty': qty}
                        self.net_pnls[symbol] = self.net_pnls.get(symbol, 0) + pnl
                        net_pnl_lbl.config(text=f"₹{self.net_pnls[symbol]:+.2f}", fg=pnl_color)
                        print(
                            f"SELL {symbol} at {sell_price:.2f} | Qty: {qty} | PnL: {pnl:+.2f} (Charges: {charges:.2f})")
                        del self.positions[symbol]
                elif symbol in self.net_pnls:
                    net_pnl_lbl.config(text=f"₹{self.net_pnls[symbol]:+.2f}", fg='cyan')
                    live_pnl_lbl.config(text="--", fg='white')
                    net_pnl_total += self.net_pnls[symbol]
                else:
                    live_pnl_lbl.config(text="--", fg='white')
                    net_pnl_lbl.config(text="₹0.00", fg='white')

        # Sort rows by change percentage
        if self.change_data:
            self.sort_rows_by_change()

        self.net_pnl_lbl.config(text=f"Net PnL: ₹{net_pnl_total:.2f}")
        self.root.after(1000, self.update_gui)

    def check_exit_time(self):
        now = datetime.now().time()
        if now >= dtime(15, 5) and not self.market_closed:
            for symbol in list(self.positions.keys()):
                ltp = self.ltp_data.get(symbol, self.positions[symbol]['buy_price']) * 0.999
                info = self.positions[symbol]
                qty = info['qty']
                buy_price = info['buy_price']
                sell_price = ltp

                gross = (sell_price - buy_price) * qty
                turnover = (buy_price + sell_price) * qty
                buy_brokerage = min(0.0003 * buy_price * qty, 20)
                sell_brokerage = min(0.0003 * sell_price * qty, 20)
                charges = buy_brokerage + sell_brokerage + (turnover * 0.0003)
                pnl = gross - charges

                self.trade_log[symbol] = {'buy_price': buy_price, 'sell_price': sell_price, 'pnl': pnl, 'qty': qty}
                self.net_pnls[symbol] = self.net_pnls.get(symbol, 0) + pnl
                _, _, _, _, net_pnl_lbl = self.ticker_widgets[symbol]
                color = 'green' if pnl >= 0 else 'red'
                net_pnl_lbl.config(text=f"₹{self.net_pnls[symbol]:+.2f}", fg=color)
                print(f"AUTO-EXIT {symbol} at {sell_price:.2f} | Qty: {qty} | PnL: {pnl:+.2f} (Charges: {charges:.2f})")
                del self.positions[symbol]

            print("\n--- TRADE SUMMARY ---")
            for sym, t in self.trade_log.items():
                print(
                    f"{sym}: Buy={t['buy_price']:.2f}, Sell={t['sell_price']:.2f}, Qty={t['qty']}, PnL={t['pnl']:+.2f}")
            print("---------------------")
            pd.DataFrame.from_dict(self.trade_log, orient='index').to_csv(fp.trade_log_file)
            self.market_closed = True
            self.fyers.close_connection()

        self.root.after(60000, self.check_exit_time)

    def setup_fyers(self):
        self.fyers = data_ws.FyersDataSocket(
            access_token=self.access_token,
            log_path="",
            litemode=True,
            write_to_file=False,
            reconnect=True,
            on_connect=self.onopen,
            on_close=self.onclose,
            on_error=self.onerror,
            on_message=self.onmessage,
            reconnect_retry=10
        )
        self.fyers.connect()

    def onopen(self):
        self.fyers.subscribe(symbols=self.tickerList, data_type="SymbolUpdate")
        self.fyers.keep_running()

    def onmessage(self, message):
        if 'ltp' in message and 'symbol' in message:
            self.ltp_data[message['symbol']] = message['ltp']

    def onerror(self, message):
        print("WebSocket Error:", message)
        if 'invalid_symbols' in message:
            self.invalid_symbols = message['invalid_symbols']
            for sym in self.invalid_symbols:
                if sym in self.tickerList:
                    self.tickerList.remove(sym)
                if sym in self.ticker_widgets:
                    row, *_ = self.ticker_widgets[sym]
                    row.destroy()
                    del self.ticker_widgets[sym]
            print("Removed invalid symbols:", self.invalid_symbols)

    def onclose(self, message):
        print("Connection closed:", message)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = FyersLiveTracker()
    app.run()