from fyers_apiv3 import fyersModel
import credentials as crs
import pandas as pd
import time
from datetime import datetime, timedelta,date
import file_paths as fp

client_id = crs.client_id
with open(fp.access_token_file) as file:
    access_token = file.read().strip()

fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path=fp.fyers_log_path)

def fetch(tickerList):
    sdict = dict()
    dat = date.today().strftime("%Y-%m-%d")
    for ticker in tickerList:
        data = {
            "symbol": ticker,
            "resolution": "1D",
            "date_format": "1",
            "range_from": dat,
            "range_to": dat,
            "cont_flag": "1"
        }

        sdata = fyers.history(data=data)
        if sdata['s'] == 'ok':
            sdict[ticker] = sdata["candles"][0][1]

        time.sleep(0.1)

    return sdict




