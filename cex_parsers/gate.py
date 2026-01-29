import requests
import asyncio
import aiohttp
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()
kyiv_tz = ZoneInfo("Europe/Kyiv")

ACCOUNT_STATS_URL = f'https://www.gate.com/apiw/v2/futures/usdt/accounts'
TOKEN_STATS_URL = f'https://www.gate.com/apiw/v2/futures/usdt/order_book'



async def get_json_summary_data() -> dict:
    if os.path.exists('output_gate/summary.json') and os.path.getsize('output_gate/summary.json') > 0:
        with open('output_gate/summary.json', 'r') as f:
            data = json.load(f)
        return data
    else:
        with open('output_gate/summary.json', 'w') as f:
            data = {
                'gate_account_stats': []
            }
            json.dump(data, f)
        return data

async def get_json_results_data() -> dict:
    if os.path.exists('output_gate/token_results.json') and os.path.getsize('output_gate/token_results.json') > 0:
        with open('output_gate/token_results.json', 'r') as f:
            data = json.load(f)
        return data
    else:
        with open('output_gate/token_results.json', 'w') as f:
            data = {
                'token_stats': []
            }
            json.dump(data, f, indent=4)
        return data

async def get_account_stats(json_summary: dict) -> dict:
    headers = {'Cookie': os.getenv('GATE_COOKIES')}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ACCOUNT_STATS_URL, headers=headers) as response:
                data = await response.json()
                pnl = data['data'][0]['history']['pnl']
                unrealised_pnl = data['data'][0]['unrealised_pnl']
                total_usd = data['data'][0]['total']
                starting_balance = data['data'][0]['history']['dnw']
                datetime_now = datetime.now(tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
                result = {
                    'datetime': datetime_now,
                    'pnl': pnl, 
                    'unrealised_pnl': unrealised_pnl, 
                    'total_usd': total_usd, 
                    'starting_balance': starting_balance
                }
                json_summary['gate_account_stats'].append(result)
                with open('output_gate/summary.json', 'w') as f:
                    json.dump(json_summary, f, indent=4)
                print(result)
                return result
    except Exception as e:
        print('Error: ', e)

async def get_token_price(token: str, json_results: dict) -> float:
    params = {
        'limit': '1',
        'contract': f'{token}_USDT',
        'interval': '0.00001'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TOKEN_STATS_URL, params=params) as response:
                data = await response.json()
                if data:
                    price = data['data']['asks'][0]['p']
                    unix_timestamp = data['data']['current']
                    datetime_now = datetime.fromtimestamp(unix_timestamp, tz=kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")
                    json_result = {
                        'token': token,
                        'price': price,
                        'datetime': datetime_now
                    }
                    json_results['token_stats'].append(json_result)
                    with open('output_gate/token_results.json', 'w') as f:
                        json.dump(json_results, f, indent=4)
                    return price
                else:
                    print('Got an error while processing...')
    except (TypeError):
        print('Invalid token ticker')

async def main():
    token = input(f"Enter token's ticker:").upper()
    token_data = await get_json_results_data()
    price = await get_token_price(token, token_data)
    print(price)
    data = await get_json_summary_data()
    await get_account_stats(data)

if __name__ == '__main__':
    asyncio.run(main())

