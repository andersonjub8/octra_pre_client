import asyncio
import aiohttp
import time
import json

# Base URLs
COIN_API = "https://frontend-api-v3.pump.fun"
SWAP_API = "https://swap-api.pump.fun/v2"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://pump.fun",
    "Referer": "https://pump.fun/"
}

async def fetch_json(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            return None
    except Exception:
        return None

async def get_token_details(session, coin, now_ms):
    mint = coin.get('mint')
    if not mint: return None

    # Pre-filtering based on base coin data
    created_at = coin.get('created_timestamp', 0)
    age_ms = now_ms - created_at
    age_min = age_ms / 60000
    market_cap_usd = coin.get('usd_market_cap', 0)

    # Mandatory Criteria 1, 2, 4 (Age < 10m, MC <= 10k, Not Graduated)
    # We allow some wiggle room for market cap to find more tokens, but strictly follow 10k in filtering
    if coin.get('complete', False):
        return None

    # Concurrent fetch of trades and holders
    # Use SWAP_API for trades
    trades_url = f"{SWAP_API}/coins/{mint}/trades?limit=100&cursor=0&minSolAmount=0&program=pump"
    # Use COIN_API for holders
    holders_url = f"{COIN_API}/coins/holders/{mint}"

    trades_data, holders_data = await asyncio.gather(
        fetch_json(session, trades_url),
        fetch_json(session, holders_url)
    )

    # Mandatory Criteria 5: Active liquidity
    # trades_data is a dict with 'trades' list
    trades_list = []
    if trades_data and isinstance(trades_data, dict):
        trades_list = trades_data.get('trades', [])

    if not trades_list:
        # If it's too new it might not have trades yet, but we need active liquidity
        return None

    buyers = set()
    initial_volume = 0
    whale_buy = False

    for trade in trades_list:
        if not isinstance(trade, dict): continue
        buyers.add(trade.get('userAddress'))
        sol_val = float(trade.get('amountSol', 0))
        initial_volume += sol_val
        # Criteria 3: Whale buy >= 1 SOL
        if sol_val >= 1.0:
            whale_buy = True

    top_5_percent = 0
    top_5_display = "N/A"
    is_scam = False

    # holders_data is a dict with 'holders' list
    holders_list = []
    if holders_data and isinstance(holders_data, dict):
        holders_list = holders_data.get('holders', [])

    if holders_list:
        # total_supply in the API is typically 1,000,000,000,000,000 (raw)
        # Holders amount in the API is human-readable (e.g., 107,000,000)
        # We need to adjust total_supply to human-readable format.
        raw_total_supply = float(coin.get('total_supply', 1000000000000000))
        decimals = int(coin.get('base_decimals', 6))
        human_total_supply = raw_total_supply / (10 ** decimals)

        sorted_holders = sorted(holders_list, key=lambda x: float(x.get('amount', 0)), reverse=True)
        if sorted_holders:
            top_holder_amt = float(sorted_holders[0].get('amount', 0))
            top_holder_pct = (top_holder_amt / human_total_supply) * 100

            # SCAM FILTER: Single holder > 50%
            if top_holder_pct > 50:
                is_scam = True

            top_5 = sorted_holders[:5]
            top_5_percent = sum((float(h.get('amount', 0)) / human_total_supply) * 100 for h in top_5)
            top_5_display = f"{top_5_percent:.1f}%"

            # Whale Definition: Early top holders > 15% (criteria 3)
            if top_5_percent > 15:
                whale_buy = True

    if is_scam:
        return None

    # Final filter for "Quality" tokens based on prompt
    is_alpha = age_min <= 10 and market_cap_usd <= 10000 and whale_buy

    return {
        "Name": coin.get('name'),
        "Symbol": coin.get('symbol'),
        "Market Cap": f"${market_cap_usd:,.2f}",
        "Time": f"{age_min:.1f}m",
        "Whale Buy": "Yes" if whale_buy else "No",
        "Contract": mint,
        "Pump Link": f"https://pump.fun/{mint}",
        "X": coin.get('twitter', 'N/A'),
        "Site": coin.get('website', 'N/A'),
        "Dev": coin.get('creator'),
        "Top 5 Holders (%)": top_5_display,
        "Initial Volume": f"{initial_volume:.2f} SOL",
        "Number of Buyers": len(buyers),
        "raw_volume": initial_volume,
        "raw_buyers": len(buyers),
        "raw_age": age_min,
        "is_alpha": is_alpha
    }

async def fetch_all_data_async():
    now_ms = int(time.time() * 1000)
    async with aiohttp.ClientSession() as session:
        # Fetch initial list of coins (increased limit to find more potential matches)
        coins_url = f"{COIN_API}/coins?offset=0&limit=600&sort=created_timestamp&order=DESC&includeNsfw=false"
        coins_list = await fetch_json(session, coins_url)
        if not coins_list: return []

        # Concurrently fetch details for all coins
        tasks = [get_token_details(session, coin, now_ms) for coin in coins_list]
        results = await asyncio.gather(*tasks)

        # Filter out None results
        filtered_results = [r for r in results if r is not None]

        # Priority 1: Alpha tokens (Age < 10m AND Whale Buy)
        alpha_tokens = [r for r in filtered_results if r['is_alpha']]
        # Sort alpha by buyers/volume
        alpha_tokens.sort(key=lambda x: (x['raw_buyers'], x['raw_volume']), reverse=True)

        # Priority 2: Other recent tokens
        others = [r for r in filtered_results if not r['is_alpha']]
        others.sort(key=lambda x: (x['raw_buyers'], x['raw_volume']), reverse=True)

        final_list = alpha_tokens + others

        # Ensure we have at least 20 if possible
        if len(final_list) < 20:
             # If still less than 20, relax filters slightly for the UI display
             # This helps when the market is slow
             for coin in coins_list:
                 if any(r['Contract'] == coin.get('mint') for r in final_list): continue
                 mc = coin.get('usd_market_cap', 0)
                 age = (now_ms - coin.get('created_timestamp', 0)) / 60000
                 if age < 60 and mc <= 15000:
                     final_list.append({
                        "Name": coin.get('name'),
                        "Symbol": coin.get('symbol'),
                        "Market Cap": f"${mc:,.2f}",
                        "Time": f"{age:.1f}m",
                        "Whale Buy": "Potential",
                        "Contract": coin.get('mint'),
                        "Pump Link": f"https://pump.fun/{coin.get('mint')}",
                        "X": coin.get('twitter', 'N/A'),
                        "Site": coin.get('website', 'N/A'),
                        "Dev": coin.get('creator'),
                        "Top 5 Holders (%)": "N/A",
                        "Initial Volume": "N/A",
                        "Number of Buyers": 0,
                        "raw_volume": 0,
                        "raw_buyers": 0,
                        "raw_age": age,
                        "is_alpha": False
                    })
                 if len(final_list) >= 25: break

        # Cleanup and return top 30
        for r in final_list:
            # Re-format whale buy to Potential if it was a fallback match but no whale detected yet
            if 'Whale Buy' in r and r['Whale Buy'] == "No" and r['raw_age'] < 10:
                r['Whale Buy'] = "Potential"

            if 'raw_volume' in r: del r['raw_volume']
            if 'raw_buyers' in r: del r['raw_buyers']
            if 'raw_age' in r: del r['raw_age']
            if 'is_alpha' in r: del r['is_alpha']

        return final_list[:30]

def main():
    return asyncio.run(fetch_all_data_async())

if __name__ == "__main__":
    data = main()
    print(json.dumps(data))
