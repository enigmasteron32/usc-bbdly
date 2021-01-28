import sys
sys.path.insert(0,'..')
from data.whale_data import find_exchange_txs
from plot.plotly_helper import plot_using_plotly
from .binance_draw import get_kline_data_from_binance

in_type = "IN"
out_type = "OUT"

# 保存最早的交易时间
from datetime import datetime
from datetime import timedelta
the_earliest_tx_time = datetime.now()

def update_y_array(X,y,timestamp,amount):
    target_index = 0
    for i in range(len(X)):
        x_time = X[i]
        if timestamp < x_time:
            target_index = i
            break

    for i in range(target_index,len(y)):
        y[i] += amount

    return y

def update_y_daily_array(X,y,timestamp,amount):
    target_index = 0
    for i in range(len(X)):
        x_time = X[i]
        if timestamp < x_time:
            target_index = i
            break
    y[target_index] += amount
    return y

def main_business_logic(client):
    txs = find_exchange_txs()

    # 找到最早的交易时间
    global the_earliest_tx_time

    for acc in txs:
        print(acc)

        acc_txs = txs[acc]
        for sub_tx in acc_txs:
            tx_date = sub_tx[0]
            if tx_date < the_earliest_tx_time: the_earliest_tx_time = tx_date

    # build X time array
    the_earliest_tx_time = the_earliest_tx_time.replace(minute=0, second=0)
    current_time = datetime.now().replace(minute=0, second=0)
    tmp_time = the_earliest_tx_time
    X = []

    while tmp_time < current_time:
        X.append(tmp_time)
        tmp_time += timedelta(hours=1)
    print(len(X))

    # build all traxe Y: deposit_amount, withdraw_amount
    deposit_trace_y = [0] * len(X)
    withdraw_trace_y = [0] * len(X)
    exchange_remain_amount_y = [0] * len(X)

    # Daily Stat
    deposit_daily_trace_y = [0] * len(X)
    withdraw_daily_trace_y = [0] * len(X)

    for holder in txs:
        holder_txs = txs[holder]

        for tx in holder_txs:
            [timestamp,from_a,tx_type,to_a,amount] = tx
            if tx_type == in_type:
                deposit_trace_y = update_y_array(X,deposit_trace_y,timestamp,amount)
                deposit_daily_trace_y = update_y_daily_array(X,deposit_daily_trace_y,timestamp,amount)
            else:
                withdraw_trace_y = update_y_array(X,withdraw_trace_y,timestamp,amount)
                withdraw_daily_trace_y = update_y_daily_array(X,withdraw_daily_trace_y,timestamp,amount)

    for i in range(0,len(X)):
        exchange_remain_amount_y[i] = deposit_trace_y[i] - withdraw_trace_y[i]

    # Draw the kline data from binance
    _,df,df_date = get_kline_data_from_binance(client)
    df['avg'] = df[['close', 'high','low','open']].mean(axis=1)

    price_trace = {'x':df_date,'y':df['avg'].values.tolist(),'name':"Binance Price ETH","yaxis":'y2'}
    volume_trace = {'x':df_date,'y':df['volume'].values.tolist(),'name':"Binance Volume"}

    deposit_trace = {"x":X,"y":deposit_trace_y,"name":"Exchange Deposit Amount"}
    withdraw_trace = {"x":X,"y":withdraw_trace_y,"name":"Exchange Withdraw Amount"}
    exchange_remain_amount_trace = {"x":X,"y":exchange_remain_amount_y,"name":"Exchange Remain Amount"}
    plot_using_plotly("Total RDN Exchange Analysis (Binance,Etherdelta)",[deposit_trace,withdraw_trace,exchange_remain_amount_trace,price_trace,volume_trace])

    deposit_trace = {"x":X,"y":deposit_daily_trace_y,"name":"Exchange Deposit Amount"}
    withdraw_trace = {"x":X,"y":withdraw_daily_trace_y,"name":"Exchange Withdraw Amount"}
    plot_using_plotly("Hourly RDN Exchange Analysis (Binance,Etherdelta)",[deposit_trace,withdraw_trace,price_trace])
