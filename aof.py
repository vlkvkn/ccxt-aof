import ccxt
import time
import os
import signal
import sys
from datetime import datetime
from itertools import combinations
from rich.console import Console
from rich.table import Table
from rich.live import Live

# Settings
EXCEPTIONS_FILE = 'exceptions.txt'
EXCHANGES_FILE = 'exchanges.txt'
LOG_FILE = 'logs.txt'


def load_exchanges(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Exchanges file '{filename}' not found.")
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]


def get_target_markets(exchange, target_ticker, only_futures=True):
    
    # Get target markets based on ticker and futures preference.
    # Args:
    #     exchange: CCXT exchange instance
    #     target_ticker: Target ticker (e.g., 'USDT')
    #     only_futures: If True, return only futures markets    
    # Returns:
    #     Set of market symbols matching criteria

    markets = exchange.load_markets()
    target_pairs = set()
    
    for symbol, market_info in markets.items():
        # Check if pair ends with target ticker
        if symbol.endswith(f'{target_ticker}'):
            # log(f'{symbol} {get_market_type(market_info)}')
            # If futures are enabled, add only futures pairs
            if only_futures:
                if (market_info.get('future', False) or market_info.get('swap', False)):
                    target_pairs.add(symbol)
            # If futures are disabled, add only spot pairs
            else:
                if not market_info.get('future', False) and not market_info.get('swap', False):
                    target_pairs.add(symbol)
    
    return target_pairs


def load_exceptions(filename):
    if not os.path.exists(filename):
        return set(), set()
    pair_exceptions = set()
    coin_exceptions = set()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            # Remove comments and spaces
            line = line.split('#', 1)[0].replace(' ', '').strip()
            if not line:
                continue
            if '/' in line:
                pair_exceptions.add(line)
            else:
                coin_exceptions.add(line)
    return pair_exceptions, coin_exceptions


def log(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{now}] {msg}')


def log_to_file(msg):
    #Log message to file
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{now}] {msg}\n')


def get_volume(volume1, volume2):
    if volume1 is None or volume2 is None:
        return 'Undefined'
    return min(volume1, volume2)


def get_real_volume_from_orderbook(exchange, symbol, price, side, max_depth=10):

    # Get real available volume at specific price from order book.
    # Args:
    #     exchange: CCXT exchange instance
    #     symbol: Trading pair symbol
    #     price: Target price
    #     side: 'asks' or 'bids'
    #     max_depth: Maximum order book depth to analyze
    # Returns:
    #     Available volume at specified price

    try:
        # Fetch order book
        orderbook = exchange.fetchOrderBook(symbol, max_depth)
        orders = orderbook[side]
        # Find orders at or below our target price
        available_volume = 0
        for entry in orders:
            level_price = entry[0]
            level_amount = entry[1]
            if level_price is None or level_amount is None:
                continue
            if level_price <= price:
                available_volume += level_amount
            else:
                break
        return available_volume

    except Exception as e:
        log(f'Error fetching orderbook for {symbol} on {exchange.id}: {e}')
        return 0.0


def calculate_arbitrage_volume(exchange1, exchange2, symbol, price1, price2):
    
    # Calculate maximum arbitrage volume based on real order book data.
    # Args:
    #     exchange1: First exchange instance
    #     exchange2: Second exchange instance
    #     symbol: Trading pair symbol
    #     price1: Price on first exchange
    #     price2: Price on second exchange
    # Returns:
    #     Maximum available volume for arbitrage

    try:
        # Get real volumes from order books
        volume1 = get_real_volume_from_orderbook(exchange1, symbol, price1, 'asks')
        volume2 = get_real_volume_from_orderbook(exchange2, symbol, price2, 'bids')
        
        # Return minimum volume (bottleneck)
        return min(volume1, volume2)
        
    except Exception as e:
        log(f'Error calculating arbitrage volume for {symbol}: {e}')
        return 0.0


def get_market_type(market_info):
    #Determine market type for display
    return market_info.get('type').upper()


def signal_handler(signum, frame):
    #Handle Ctrl+C gracefully
    print("\n\nExiting gracefully...")
    sys.exit(0)


def main():
    console = Console()
    
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load exchanges from file
    EXCHANGES = load_exchanges(EXCHANGES_FILE)
    
    # Request target ticker from user
    TARGET_TICKER = input("Enter target ticker (default USDT): ").strip().upper()
    if not TARGET_TICKER:
        TARGET_TICKER = 'USDT'
    
    # Ask about including futures
    FUTURES_ONLY = input("Include only futures/swap markets (1) or only spot markets (2)? (default 1): ").strip().lower()
    FUTURES_ONLY = FUTURES_ONLY != '2'
    
    # Ask about order book analysis
    ORDERBOOK_ANALYSIS = input("Enable detailed order book analysis for real volumes? (y/n, default: n): ").strip().lower()
    ORDERBOOK_ANALYSIS = ORDERBOOK_ANALYSIS == 'y'
    
    DELTA = 0.02 # 2%
    DELTA_INPUT = input("Enter minimum delta in percentage (default 2%): ")
    if DELTA_INPUT:
        DELTA = int(DELTA_INPUT) / 100.0

    CHECK_INTERVAL = 2  # 2 seconds
    CHECK_INTERVAL_INPUT = input("Enter update interval in seconds (default 2): ")
    if CHECK_INTERVAL_INPUT:
        CHECK_INTERVAL = int(CHECK_INTERVAL_INPUT)
    
    log(f'Target ticker: {TARGET_TICKER}')
    log(f'Order book analysis: {"Enabled" if ORDERBOOK_ANALYSIS else "Disabled"}')
    log(f'Minimum delta: {DELTA * 100:.2f}%')
    log(f'Update interval: {CHECK_INTERVAL}sec.')
    log(f'Exchanges for arbitrage (ccxt): {EXCHANGES}')
    
    if FUTURES_ONLY:
        log('Mode: FUTURES/SWAP markets only')
    else:
        log('Mode: SPOT markets only')

    exchange_objs = {}
    for ex in EXCHANGES:
        try:
            exchange_objs[ex] = getattr(ccxt, ex)()
        except Exception as e:
            log(f'Initialization error {ex}: {e}')
    
    # Get pairs with TARGET_TICKER
    markets_by_exchange = {}
    market_info_by_exchange = {}
    for ex, obj in exchange_objs.items():
        try:
            markets_by_exchange[ex] = get_target_markets(obj, TARGET_TICKER, FUTURES_ONLY)
            # Save market information for determining type
            if markets_by_exchange[ex]:
                market_info_by_exchange[ex] = obj.load_markets()
        except Exception as e:
            log(f'Error loading pairs {ex}: {e}')
            markets_by_exchange[ex] = set()
            market_info_by_exchange[ex] = {}

    # Collect all unique pairs
    all_pairs = set()
    for pairs in markets_by_exchange.values():
        all_pairs.update(pairs)

    # Load exceptions
    pair_exceptions, coin_exceptions = load_exceptions(EXCEPTIONS_FILE)
    if pair_exceptions or coin_exceptions:
        log(f'Excluded pairs: {sorted(pair_exceptions)}')
        log(f'Excluded coins: {sorted(coin_exceptions)}')
    filtered_pairs = set()
    for pair in all_pairs:
        base, _, quote = pair.partition('/')
        if pair in pair_exceptions:
            continue
        if base in coin_exceptions or quote in coin_exceptions:
            continue
        filtered_pairs.add(pair)
    if not filtered_pairs:
        log('No pairs to check after applying exceptions.')
        return

    # Pre-calculate exchange intersections for each pair
    pair_exchanges = {}
    for symbol in filtered_pairs:
        pair_exchanges[symbol] = [ex for ex in EXCHANGES if symbol in markets_by_exchange.get(ex, set())]
    # Keep only pairs that exist on at least two exchanges
    valid_pairs = {symbol for symbol, exs in pair_exchanges.items() if len(exs) >= 2}
    log(f'Pairs to check: {sorted(valid_pairs)}')
    
    # For storing results
    results = []
    
    # Generate all possible pair comparisons
    pair_combos = []
    for symbol in sorted(valid_pairs):
        available_exs = pair_exchanges[symbol]
        for ex1, ex2 in combinations(available_exs, 2):
            pair_combos.append((symbol, ex1, ex2))
    
    # Create table
    def make_table():
        table = Table(title=f"Arbitrage opportunities ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        table.add_column("Pair")
        table.add_column("Market Type")
        table.add_column("Buy Exchange")
        table.add_column("Buy Price")
        table.add_column("Sell Exchange")
        table.add_column("Sell Price")
        table.add_column("Volume")
        table.add_column("Profit %")
        
        for result in results:
            symbol, market_type, buy_ex, buy_price, sell_ex, sell_price, volume, profit_pct = result
            table.add_row(
                symbol, 
                market_type, 
                buy_ex, 
                str(buy_price), 
                sell_ex, 
                str(sell_price), 
                str(volume), 
                f"{profit_pct*100:.2f}%"
            )
        return table
    
    with Live(make_table(), refresh_per_second=2, console=console) as live:
        try:
            while True:
                tickers_by_exchange = {}
                for ex, obj in exchange_objs.items():
                    try:
                        pairs_for_exchange = list(markets_by_exchange[ex] & valid_pairs)
                        tickers_by_exchange[ex] = obj.fetch_tickers(pairs_for_exchange)
                    except Exception as e:
                        log(f'Bulk request error {ex}: {e}')
                        tickers_by_exchange[ex] = {}
                
                results.clear()
                
                for symbol, ex1, ex2 in pair_combos:
                    t1 = tickers_by_exchange[ex1].get(symbol, {})
                    t2 = tickers_by_exchange[ex2].get(symbol, {})
                    
                    # Get market type information
                    market_type1 = get_market_type(market_info_by_exchange.get(ex1, {}).get(symbol, {}))
                    market_type2 = get_market_type(market_info_by_exchange.get(ex2, {}).get(symbol, {}))
                    
                    # Check arbitrage opportunity: buy on ex2, sell on ex1
                    if not (t1.get('bid') is None or t2.get('ask') is None):
                        diff = (t1.get('bid') - t2.get('ask')) / t2.get('ask')
                        if diff > DELTA:
                            volume = 0
                            if ORDERBOOK_ANALYSIS:
                                # Get real volume from order books
                                volume = calculate_arbitrage_volume(exchange_objs[ex2], exchange_objs[ex1],symbol, t2.get('ask'), t1.get('bid'))
                            else:
                                volume = get_volume(t1.get('bidVolume'), t2.get('askVolume'))

                            if (not ORDERBOOK_ANALYSIS) or volume > 0:
                                results.append((symbol, market_type2, ex2, t2.get('ask'), ex1, t1.get('bid'), volume, diff))
                                log_to_file(f"{symbol} ({market_type2}) - BUY on {ex2} at {t2.get('ask')}, SELL on {ex1} at {t1.get('bid')}, Volume: {volume}, Profit: {diff*100:.2f}%")

                    # Check arbitrage opportunity: buy on ex1, sell on ex2
                    if not (t2.get('bid') is None or t1.get('ask') is None):
                        diff = (t2.get('bid') - t1.get('ask')) / t1.get('ask')
                        if diff > DELTA:
                            volume = 0
                            if ORDERBOOK_ANALYSIS:
                                # Get real volume from order books
                                volume = calculate_arbitrage_volume(exchange_objs[ex1], exchange_objs[ex2],symbol, t1.get('ask'), t2.get('bid'))
                            else:
                                volume = get_volume(t2.get('bidVolume'), t1.get('askVolume'))

                            if (not ORDERBOOK_ANALYSIS) or volume > 0: 
                                results.append((symbol, market_type1, ex1, t1.get('ask'), ex2, t2.get('bid'), volume, diff))
                                log_to_file(f"{symbol} ({market_type1}) - BUY on {ex1} at {t1.get('ask')}, SELL on {ex2} at {t2.get('bid')}, Volume: {volume}, Profit: {diff*100:.2f}%")
                
                # Sort results by profitability
                results.sort(key=lambda x: x[7], reverse=True)
                
                live.update(make_table())
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\nExiting gracefully...")
            sys.exit(0)


if __name__ == '__main__':
    main() 