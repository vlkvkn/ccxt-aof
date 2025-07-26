# CCXT Arbitrage Checker

A real-time cryptocurrency arbitrage opportunity finder that monitors multiple exchanges simultaneously to identify profitable trading opportunities.

## Features

- **Multi-Exchange Support**: Monitors Binance, Bybit, and OKX exchanges
- **Real-Time Monitoring**: Continuously checks for price differences across exchanges
- **Customizable Parameters**: 
  - Target ticker (USDT, BTC, ETH, etc.)
  - Minimum delta percentage
  - Update interval
- **Exception Management**: Exclude specific coins or trading pairs

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vlkvkn/ccxt-arbitrage-ability-parser.git
cd ccxt-arbitrage
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the program:
```bash
python arbitrage_checker.py
```

2. Follow the interactive prompts:
   - Enter target ticker (default: USDT)
   - Enter minimum delta percentage (default: 3%)
   - Enter update interval in seconds (default: 2)

3. The program will start monitoring and display arbitrage opportunities in a live table.

4. Press `Ctrl+C` to exit.

## Configuration

### Exceptions File

Create an `exceptions.txt` file to exclude specific coins or trading pairs:

```
# You can enter either a Ticker, e.g. "DOGS", or a Symbol, e.g. "DOGS/USDT"
NEIRO # different coins under the same ticker
ALPHA # different coins under the same ticker
MOVE # expensive, slow deposit/withdrawal only via Ethereum network
```

## How It Works

1. **Exchange Connection**: Connects to multiple cryptocurrency exchanges using CCXT library
2. **Market Data Collection**: Fetches all trading pairs for the specified target ticker
3. **Pair Filtering**: Applies exceptions and keeps only pairs available on at least 2 exchanges
4. **Price Comparison**: Continuously compares prices across exchanges
5. **Opportunity Detection**: Identifies price differences above the specified delta threshold
6. **Live Display**: Shows opportunities in a real-time updating table

## Output Example

```
Arbitrage opportunities (2025-07-26 15:42:36)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Pair       ┃ Exchange 1 ┃ Price 1 ┃ Exchange 2 ┃ Price 2 ┃ Difference % ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ AR/USDC    │ binance    │ 7.71    │ bybit      │ 7.6     │ 1.45         │
│ CATI/USDC  │ bybit      │ 0.08785 │ okx        │ 0.08885 │ 1.14         │
│ ETHFI/USDC │ binance    │ 1.215   │ okx        │ 1.1996  │ 1.28         │
└────────────┴────────────┴─────────┴────────────┴─────────┴──────────────┘
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