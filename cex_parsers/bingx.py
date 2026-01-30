import time
import requests
import hmac
import urllib.parse
from hashlib import sha256
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os
import json


load_dotenv()

kyiv_tz = ZoneInfo("Europe/Kyiv")
BINGX_APIKEY = os.getenv('BINGX_APIKEY')
BINGX_SECRETKEY = os.getenv('BINGX_SECRETKEY')

APIURL = "https://open-api.bingx.com"

async def get_token_price(token: str) -> float:
    api_data = await get_data_from_api(token)
    if api_data:
        price = await normalize_price(api_data)
        json_result = await get_old_results_data()

        # Getting time in readable format
        unix_timestamp = api_data['timestamp']
        datetime_now = datetime.fromtimestamp(unix_timestamp / 1000, tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")

        appended_data = {
            'token': token,
            'price': price,
            'datetime': datetime_now
        }

        # Appending new data to token_results.json
        await append_to_results(json_result, appended_data)

        return price
    else:
        return "Error while parsing the price"

        

async def get_data_from_api(token: str):
    payload = {}
    path = '/openApi/cswap/v1/market/premiumIndex'
    method = "GET"
    paramsMap = {
        "symbol": f"{token}-USD"
    }
    paramsStr, urlParamsStr = await parseParam(paramsMap)
    data = await send_request(method, path, paramsStr, urlParamsStr, payload)
    return data

async def normalize_price(data: dict):
    price = data['data'][0]['markPrice']
    return price

async def append_to_results(old_data: dict, data_to_append: dict):
    old_data['token_stats'].append(data_to_append)
    with open('output_bingx/token_results.json', 'w') as f:
        json.dump(old_data, f, indent=4)


async def get_account_stats() -> dict:
    payload = {}
    path = '/openApi/account/v1/allAccountBalance'
    method = "GET"
    paramsMap = {
        "recvWindow": "6000"
    }
    paramsStr, urlParamsStr = await parseParam(paramsMap)

    data = await send_request(method, path, paramsStr, urlParamsStr, payload)
    print(data)
    json_result = await get_json_summary_data()

    balances = data['data']
    appended_data = {}
    for balance_type in balances:
        balance = float(balance_type['usdtBalance'])
        if balance > 0:
            if balance_type['accountType'] == 'sopt':
                appended_data['spot'] = balance
            else:
                appended_data[balance_type['accountType']] = balance


    
    unix_timestamp = data['timestamp']
    datetime_now = datetime.fromtimestamp(unix_timestamp / 1000, tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
    appended_data['datetime']= datetime_now

    json_result['bingx_account_stats'].append(appended_data)
    with open('output_bingx/summary.json', 'w') as f:
        json.dump(json_result, f, indent=4)
    return data


async def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    return signature


async def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, await get_sign(BINGX_SECRETKEY, paramsStr))
    headers = {
        'X-BX-APIKEY': BINGX_APIKEY,
    }
    try:
        response = requests.request(method, url, headers=headers, data=payload)
        data = response.json()
        return data
    except Exception as e:
        print('Error:', e)

async def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


async def get_old_results_data() -> dict:
    if os.path.exists('output_bingx/token_results.json') and os.path.getsize('output_bingx/token_results.json') > 0:
        with open('output_bingx/token_results.json', 'r') as f:
            data = json.load(f)
            return data
    else:
        with open('output_bingx/token_results.json', 'w') as f:
            data = {
                'token_stats': []
            }
            json.dump(data, f, indent=4)
        return data

async def get_json_summary_data() -> dict:
    if os.path.exists('output_bingx/summary.json') and os.path.getsize('output_bingx/summary.json') > 0:
        with open('output_bingx/summary.json', 'r') as f:
            data = json.load(f)
        return data
    else:
        with open('output_bingx/summary.json', 'w') as f:
            data = {
                'bingx_account_stats': []
            }
            json.dump(data, f)
        return data


async def main():
    token = input(f"Enter token's ticker:").upper()
    price = await get_token_price(token)
    print(f"{token} price: {price}")
    await get_account_stats()


if __name__ == "__main__":
    asyncio.run(main())