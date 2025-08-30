# CCXT Arbitrage Opportunity Finder

A real-time cryptocurrency arbitrage opportunity finder that monitors multiple exchanges simultaneously to identify profitable trading opportunities.

## Features

- **Multi-Exchange Support**: Monitors multiple exchanges (configurable via exchanges.txt)
- **Real-Time Monitoring**: Continuously checks for price differences across exchanges
- **Customizable Parameters**: 
  - Target ticker (USDT, BTC, ETH, etc.)
  - Minimum delta percentage
  - Update interval
- **Exception Management**: Exclude specific coins or trading pairs

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
3. **Pair Filtering**: Applies exceptions and keeps only pairs available on at least 2 exchanges
4. **Price Comparison**: Continuously compares prices across exchanges
5. **Opportunity Detection**: Identifies price differences above the specified delta threshold
6. **Live Display**: Shows opportunities in a real-time updating table

## Output Example

```
                       Arbitrage opportunities (2025-08-30 12:48:21)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Pair     ┃ Exchange Ask ┃ Price Ask ┃ Exchange Bid ┃ Price Bid ┃ Difference % ┃ Volume  ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ BIO/USDT │ binance      │ 0.1762    │ okx          │ 0.18449   │ 4.70         │ 108.938 │
└──────────┴──────────────┴───────────┴──────────────┴───────────┴──────────────┴─────────┘
```

## Requirements

- Python 3.7+
- CCXT library
- Rich library for terminal UI

## Dependencies

- `ccxt`: Cryptocurrency exchange trading library
- `rich`: Rich text and beautiful formatting in the terminal
- `datetime`: Date and time utilities
- `itertools`: Efficient looping tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


## Disclaimer

This tool is for educational and informational purposes only. Cryptocurrency trading involves significant risk. Always do your own research and consider consulting with a financial advisor before making any trading decisions.