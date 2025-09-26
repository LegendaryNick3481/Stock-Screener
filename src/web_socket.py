import tkinter as tk
from fyers_apiv3.FyersWebsocket import data_ws
import pandas as pd
import credentials as crs
import screener
import fetch_open
from datetime import datetime, time as dtime
import math
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
        self.traded_today = set()  # 🆕 Added to track traded symbols

        self.capital_per_stock = 500 * 5  # ₹2500 with 5x margin

        self.ticker_df = pd.read_csv(fp.ticker_data_file)
        self.tickerList = self.ticker_df['Symbol'].tolist()

        with open(fp.access_token_file) as file:
            self.access_token = file.read().strip()

        self.setup_gui()
        self.setup_fyers()

    def calculate_pnl_with_costs(self, buy_price, sell_price, qty):
        turnover = (buy_price + sell_price) * qty
        brokerage = min(20, 0.0003 * turnover)
        charges = 0.001 * turnover
        slippage = 0.001 * turnover
        total_cost = brokerage + charges + slippage
        gross_pnl = (sell_price - buy_price) * qty
        net_pnl = gross_pnl - total_cost
        return net_pnl, gross_pnl, total_cost

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

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

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
            self.open_fetched = True
            print("[INFO] Fetched open prices")
        else:
            self.root.after(1000, self.fetch_open_prices_if_market_open)

    def create_header(self):
        header = tk.Frame(self.scrollable_frame, bg='black')
        header.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(header, text="Ticker", fg='white', bg='black', width=15, anchor='w', font=('Consolas', 12, 'bold')).pack(side=tk.LEFT)
        tk.Label(header, text="LTP", fg='white', bg='black', width=10, anchor='e', font=('Consolas', 12, 'bold')).pack(side=tk.RIGHT)
        tk.Label(header, text="% Change", fg='white', bg='black', width=10, anchor='e', font=('Consolas', 12, 'bold')).pack(side=tk.RIGHT, padx=(10, 0))
        tk.Label(header, text="Live PnL", fg='white', bg='black', width=10, anchor='e', font=('Consolas', 12, 'bold')).pack(side=tk.RIGHT, padx=(10, 0))
        tk.Label(header, text="Net PnL", fg='white', bg='black', width=10, anchor='e', font=('Consolas', 12, 'bold')).pack(side=tk.RIGHT, padx=(10, 0))

    def create_rows(self):
        for ticker in self.tickerList:
            row = tk.Frame(self.scrollable_frame, bg='black')

            lbl = tk.Label(row, text=ticker.split(":")[-1], fg='white', bg='black', width=15, anchor='w', font=('Consolas', 12))
            lbl.pack(side=tk.LEFT)

            ltp_lbl = tk.Label(row, text="--", fg='lime', bg='black', width=10, anchor='e', font=('Consolas', 12, 'bold'))
            ltp_lbl.pack(side=tk.RIGHT)

            change_lbl = tk.Label(row, text="--", fg='yellow', bg='black', width=10, anchor='e', font=('Consolas', 12))
            change_lbl.pack(side=tk.RIGHT, padx=(10, 0))

            live_pnl_lbl = tk.Label(row, text="--", fg='white', bg='black', width=10, anchor='e', font=('Consolas', 12))
            live_pnl_lbl.pack(side=tk.RIGHT, padx=(10, 0))

            net_pnl_lbl = tk.Label(row, text="₹0.00", fg='cyan', bg='black', width=10, anchor='e', font=('Consolas', 12))
            net_pnl_lbl.pack(side=tk.RIGHT, padx=(10, 0))

            self.ticker_widgets[ticker] = (row, ltp_lbl, change_lbl, live_pnl_lbl, net_pnl_lbl)
            row.pack(fill=tk.X, padx=10, pady=2)

    def update_gui(self):
        if self.market_closed or not self.open_fetched:
            self.root.after(1000, self.update_gui)
            return

        net_pnl_total = 0
        now_time = datetime.now().time()

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

                if change >= 3 and symbol not in self.positions and symbol not in self.traded_today and now_time <= dtime(10, 30):
                    qty = max(1, int(self.capital_per_stock / ltp))
                    self.positions[symbol] = {
                        'buy_price': ltp,
                        'buy_time': datetime.now().strftime("%H:%M:%S"),
                        'qty': qty
                    }
                    print(f"BUY {symbol} at {ltp:.2f} | Qty: {qty} | Change: {change:.2f}% | Time: {self.positions[symbol]['buy_time']}")

                if symbol in self.positions:
                    buy = self.positions[symbol]
                    live_pnl, gross_pnl, cost = self.calculate_pnl_with_costs(
                        buy_price=buy['buy_price'],
                        sell_price=ltp,
                        qty=buy['qty']
                    )
                    pnl_color = 'green' if live_pnl >= 0 else 'red'
                    live_pnl_lbl.config(text=f"{live_pnl:+.2f}", fg=pnl_color)
                    net_pnl_total += live_pnl

                    if ltp <= buy['buy_price'] * 0.995:
                        exit_time = datetime.now().strftime("%H:%M:%S")
                        pnl, gross_pnl, cost = self.calculate_pnl_with_costs(
                            buy_price=buy['buy_price'],
                            sell_price=ltp,
                            qty=buy['qty']
                        )
                        self.trade_log[symbol] = {
                            'buy_price': buy['buy_price'],
                            'sell_price': ltp,
                            'pnl': pnl,
                            'gross_pnl': gross_pnl,
                            'costs': cost,
                            'qty': buy['qty'],
                            'entry_time': buy['buy_time'],
                            'exit_time': exit_time
                        }
                        self.net_pnls[symbol] = self.net_pnls.get(symbol, 0) + pnl
                        self.traded_today.add(symbol)  # 🆕 Mark as traded
                        color = 'green' if pnl >= 0 else 'red'
                        net_pnl_lbl.config(text=f"₹{self.net_pnls[symbol]:+.2f}", fg=color)
                        print(f"SELL {symbol} at {ltp:.2f} | Qty: {buy['qty']} | PnL: {pnl:+.2f} | Exit Time: {exit_time}")
                        del self.positions[symbol]

                elif symbol in self.net_pnls:
                    net_pnl_lbl.config(text=f"₹{self.net_pnls[symbol]:+.2f}", fg='cyan')
                    live_pnl_lbl.config(text="--", fg='white')
                    net_pnl_total += self.net_pnls[symbol]
                else:
                    live_pnl_lbl.config(text="--", fg='white')
                    net_pnl_lbl.config(text="₹0.00", fg='white')
            else:
                self.change_data[symbol] = None
                change_lbl.config(text="--", fg='yellow')

        sorted_symbols = sorted(
            [s for s in self.ticker_widgets if self.change_data.get(s) is not None],
            key=lambda s: self.change_data[s],
            reverse=True
        )

        for symbol in sorted_symbols:
            row, *_ = self.ticker_widgets[symbol]
            row.pack_forget()
            row.pack(fill=tk.X, padx=10, pady=2)

        self.net_pnl_lbl.config(text=f"Net PnL: ₹{net_pnl_total:.2f}")
        self.root.after(2000, self.update_gui)

    def check_exit_time(self):
        now = datetime.now().time()
        if now >= dtime(15, 5) and not self.market_closed:
            for symbol in list(self.positions.keys()):
                ltp = self.ltp_data.get(symbol, self.positions[symbol]['buy_price'])
                info = self.positions[symbol]
                exit_time = datetime.now().strftime("%H:%M:%S")
                pnl, gross_pnl, cost = self.calculate_pnl_with_costs(
                    buy_price=info['buy_price'],
                    sell_price=ltp,
                    qty=info['qty']
                )
                self.trade_log[symbol] = {
                    'buy_price': info['buy_price'],
                    'sell_price': ltp,
                    'pnl': pnl,
                    'gross_pnl': gross_pnl,
                    'costs': cost,
                    'qty': info['qty'],
                    'entry_time': info['buy_time'],
                    'exit_time': exit_time
                }
                self.net_pnls[symbol] = self.net_pnls.get(symbol, 0) + pnl
                self.traded_today.add(symbol)  # 🆕 Mark as traded on auto-exit
                _, _, _, _, net_pnl_lbl = self.ticker_widgets[symbol]
                color = 'green' if pnl >= 0 else 'red'
                net_pnl_lbl.config(text=f"₹{self.net_pnls[symbol]:+.2f}", fg=color)
                print(f"AUTO-EXIT {symbol} at {ltp:.2f} | Qty: {info['qty']} | PnL: {pnl:+.2f} | Exit Time: {exit_time}")
                del self.positions[symbol]

            print("\n--- TRADE SUMMARY ---")
            for sym, t in self.trade_log.items():
                print(f"{sym}: Buy={t['buy_price']:.2f}, Sell={t['sell_price']:.2f}, Qty={t['qty']}, "
                      f"Gross PnL={t['gross_pnl']:+.2f}, Cost={t['costs']:.2f}, Net PnL={t['pnl']:+.2f}, "
                      f"Entry={t['entry_time']}, Exit={t['exit_time']}")
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
