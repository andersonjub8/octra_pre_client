# PumpHunter 🚀

PumpHunter is a specialized on-chain analysis tool for identifying new and promising token launches on [Pump.fun](https://pump.fun/). It monitors the Solana blockchain to find tokens that meet specific "Alpha" criteria.

## Features

- **Real-Time Monitoring**: identifies tokens created less than 10 minutes ago.
- **Market Cap Filtering**: Filters for tokens with a market cap ≤ $10,000 USD.
- **Whale Detection**: Flags tokens with significant buy transactions (≥ 1 SOL) or strong early holder distribution.
- **Scam Filter**: Automatically ignores tokens where a single holder owns more than 50% of the supply.
- **Social Links**: Extracts X (Twitter) profiles and project websites from token metadata.
- **Activity Metrics**: Tracks the number of unique buyers and initial trading volume.

## Requirements

- Python 3.8+
- Flask
- Requests

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/andersonjub8/PumpHunter.git
   cd PumpHunter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To start the PumpHunter dashboard:

```bash
python3 app.py
```

The application will be available at `http://localhost:3000`.

## Methodology

PumpHunter uses the Pump.fun frontend API to fetch the most recent token launches. It then enriches this data by querying trade history and holder distribution for each candidate. Tokens are sorted by recent activity and buyer count to highlight the most trending opportunities.
