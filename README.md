# CCXT Arbitrage Opportunity Finder

A real-time cryptocurrency arbitrage opportunity finder that monitors multiple exchanges simultaneously to identify profitable trading opportunities.

## Features

- **Multi-Exchange Support**: Monitors multiple exchanges (configurable via exchanges.txt)
- **Market Type Support**: Works with spot, futures, and swap markets
- **Real-Time Monitoring**: Continuously checks for price differences across exchanges
- **Customizable Parameters**: 
  - Target ticker (USDT, BTC, ETH, etc.)
  - Market type selection (spot, futures, or both)
  - Minimum delta percentage
  - Update interval
- **Exception Management**: Exclude specific coins or trading pairs
- **Live Table Display**: Real-time updating table with market type information
- **Logging**: Automatic logging of arbitrage opportunities to file

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vlkvkn/ccxt-aof.git
cd ccxt-aof
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the program:
```bash
python aof.py
```

2. Follow the interactive prompts:
   - Enter target ticker (default: USDT)
   - Choose whether to include futures markets (y/n, default: y)
   - Enter minimum delta percentage (default: 3%)
   - Enter update interval in seconds (default: 2)

3. The program will start monitoring and display arbitrage opportunities in a live table.

4. Press `Ctrl+C` to exit.

## Configuration

### Exchanges File

Create an `exchanges.txt` file to specify which exchanges to monitor:

```
# ccxt supported exchanges (full list: https://docs.ccxt.com/#/Exchange-Markets)
binance
bybit
okx
kucoin
gate
```

### Exceptions File

Create an `exceptions.txt` file to exclude specific coins or trading pairs:

```
# You can enter either a Ticker, e.g. "DOGS", or a Symbol, e.g. "DOGS/USDT"
NEIRO # different coins under the same ticker
ALPHA # different coins under the same ticker
MOVE # expensive, slow deposit/withdrawal only via Ethereum network
```

## How It Works

1. **Exchange Connection**: Connects to cryptocurrency exchanges specified in exchanges.txt using CCXT library
2. **Market Data Collection**: Fetches all trading pairs for the specified target ticker
3. **Market Type Filtering**: Filters markets based on user preference (spot, futures, or both)
4. **Pair Filtering**: Applies exceptions and keeps only pairs available on at least 2 exchanges
5. **Price Comparison**: Continuously compares bid/ask prices across exchanges
6. **Opportunity Detection**: Identifies price differences above the specified delta threshold
7. **Live Display**: Shows opportunities in a real-time updating table with market type information
8. **Logging**: Automatically logs all arbitrage opportunities to logs.txt

## Output Example

```
                               Arbitrage opportunities (2025-08-31 15:40:09)
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Pair        ┃ Market Type ┃ Buy Exchange ┃ Buy Price ┃ Sell Exchange ┃ Sell Price ┃ Volume    ┃ Profit % ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ DUEL/USDT   │ SPOT        │ gate         │ 0.0005268 │ bybit         │ 0.0005431  │ Undefined │ 3.09%    │
│ PINEYE/USDT │ SPOT        │ bybit        │ 0.0002892 │ gate          │ 0.00029964 │ Undefined │ 3.61%    │
└─────────────┴─────────────┴──────────────┴───────────┴───────────────┴────────────┴───────────┴──────────┘
```

## Market Types

The program identifies and displays different market types:
- **SPOT**: Traditional spot trading markets
- **FUTURES**: Futures contracts markets
- **SWAP**: Perpetual swap markets
- **UNKNOWN**: Markets with undetermined type

## Requirements

- Python 3.7+
- CCXT library
- Rich library for terminal UI

## Dependencies

- `ccxt`: Cryptocurrency exchange trading library
- `rich`: Rich text and beautiful formatting in the 

## Logging

All arbitrage opportunities are automatically logged to `logs.txt` with timestamps:
```
[2025-08-31 15:40:09] DUEL/USDT (SPOT/SPOT) - BUY on gate at 0.0005268, SELL on bybit at 0.0005431, Volume: Undefined, Profit: 3.09%
[2025-08-31 15:40:09] PINEYE/USDT (SPOT/SPOT) - BUY on bybit at 0.0002892, SELL on gate at 0.00029964, Volume: Undefined, Profit: 3.61%
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Disclaimer

This tool is for educational and informational purposes only. Cryptocurrency trading involves significant risk. Always do your own research and consider consulting with a financial advisor before making any trading decisions. The tool does not execute trades automatically - it only identifies potential opportunities.