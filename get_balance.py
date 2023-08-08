from binance.client import Client
import local__config as local
import my_logging as mylog
import functions as fn

client = Client(local.LOC_BNC_AK, local.LOC_BNC_SK,
                    testnet=local.LOC_BNC_TESNET)

asset = 'USDT'
balance = client.get_asset_balance(asset)
print(asset,' -> ',balance)
info = client.get_exchange_info()

for dato in info:
    if dato=='symbols':
        for i in info[dato]:

            asset = i['baseAsset']
            if i['quoteAsset']=='USDT':
                balance = client.get_asset_balance(asset)
                print(asset,' -> ',balance)