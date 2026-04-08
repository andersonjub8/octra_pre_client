# PumpHunter 🚀 (Jules Platform)

PumpHunter is a specialized on-chain analysis tool for identifying token launches on [Pump.fun](https://pump.fun/). It monitors the Solana blockchain to find tokens that meet specific "Alpha" criteria.

## Features (Jules Environment)

- **Age Filter**: Monitor tokens older than 20 minutes to ensure stability.
- **Blacklist**: Automatically excludes known "scam deployer" wallets from `top_deployers_pump.csv`.
- **Market Cap Filtering**: Filters for tokens with a market cap ≤ $10,000 USD.
- **Whale Detection**: Flags tokens with significant buy transactions (≥ 1 SOL) or strong early holder distribution.
- **Scam Filter**: Automatically ignores tokens where a single holder owns more than 50% of the supply.
- **Dev Activity**: Track if the developer has sold their initial position.
- **Social Links**: Extracts X (Twitter) profiles and project websites from token metadata.
- **Activity Metrics**: Tracks the number of unique buyers and initial trading volume.

## Requirements

- Python 3.8+
- Flask
- aiohttp

## Deployment on Jules
This project is configured for the Jules environment. The server runs on port 3000 and is accessible via the Jules proxy.

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

The application will be available at `http://0.0.0.0:3000`.

## Methodology

PumpHunter uses the Pump.fun frontend API to fetch the most recent token launches. It then enriches this data by querying trade history and holder distribution for each candidate. Tokens are sorted by recent activity and buyer count to highlight the most trending opportunities.
