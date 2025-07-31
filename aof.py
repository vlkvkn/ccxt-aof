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


def load_exchanges(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Exchanges file '{filename}' not found.")
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]


def get_target_markets(exchange, target_ticker):
    markets = exchange.load_markets()
    target_pairs = set()
    for symbol in markets:
        if symbol.endswith(f'/{target_ticker}'):
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


def get_volume(volume1, volume2):
    if volume1 is None or volume2 is None:
        return 'Undefined'
    return min(volume1, volume2)


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
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
    
    DELTA = 0.03 # 3%
    DELTA_INPUT = input("Enter minimum delta in percentage (default 3%): ")
    if DELTA_INPUT:
        DELTA = int(DELTA_INPUT) / 100.0

    CHECK_INTERVAL = 2  # 2 seconds
    CHECK_INTERVAL_INPUT = input("Enter update interval in seconds (default 2): ")
    if CHECK_INTERVAL_INPUT:
        CHECK_INTERVAL = int(CHECK_INTERVAL_INPUT)
    
    log(f'Target ticker: {TARGET_TICKER}')
    log(f'Minimum delta: {DELTA * 100:.2f}%')
    log(f'Update interval: {CHECK_INTERVAL}sec.')
    log(f'Exchanges for arbitrage (ccxt): {EXCHANGES}')

    exchange_objs = {}
    for ex in EXCHANGES:
        try:
            exchange_objs[ex] = getattr(ccxt, ex)()
        except Exception as e:
            log(f'Initialization error {ex}: {e}')
    
    # Get pairs with TARGET_TICKER
    markets_by_exchange = {}
    for ex, obj in exchange_objs.items():
        try:
            markets_by_exchange[ex] = get_target_markets(obj, TARGET_TICKER)
        except Exception as e:
            log(f'Error loading pairs {ex}: {e}')
            markets_by_exchange[ex] = set()

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
    results = {}
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
        table.add_column("Exchange Ask")
        table.add_column("Price Ask")
        table.add_column("Exchange Bid")
        table.add_column("Price Bid")
        table.add_column("Difference %")
        table.add_column("Volume")
        for key, value in results.items():
            symbol, ex1, ex2 = key
            price1, price2, diff, volume = value
            table.add_row(symbol, ex1, str(price1), ex2, str(price2), f"{diff*100:.2f}", str(volume))
        return table
    with Live(make_table(), refresh_per_second=2, console=console) as live:
        try:
            while True:
                now_ms = int(time.time() * 1000)
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
                    if not (t1.get('bid') is None or t2.get('ask')  is None):
                        diff = (t1.get('bid') - t2.get('ask')) / t2.get('ask')
                        if diff > DELTA:
                            volume = get_volume(t1.get('bidVolume'), t2.get('askVolume'))
                            results[(symbol, ex2, ex1)] = (t2.get('ask'), t1.get('bid'), diff, volume)
                    if not (t2.get('bid') is None or t1.get('ask') is None):
                        diff = (t2.get('bid') - t1.get('ask')) / t1.get('ask')
                        if diff > DELTA:
                            volume = get_volume(t2.get('bidVolume'), t1.get('askVolume'))
                            results[(symbol, ex1, ex2)] = (t1.get('ask'), t2.get('bid'), diff, volume)
                live.update(make_table())
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\nExiting gracefully...")
            sys.exit(0)


if __name__ == '__main__':
    main() 