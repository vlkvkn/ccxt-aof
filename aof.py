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


def get_target_markets(exchange, target_ticker, include_futures=True):
    markets = exchange.load_markets()
    target_pairs = set()
    
    for symbol, market_info in markets.items():
        # Check if pair ends with target ticker
        if symbol.endswith(f'/{target_ticker}'):
            # If futures are enabled, add all pairs
            if include_futures:
                target_pairs.add(symbol)
            # If futures are disabled, exclude futures pairs
            elif not market_info.get('future', False) and not market_info.get('swap', False):
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


def get_market_type(market_info):
    #Determine market type for display
    if market_info.get('future', False):
        return 'FUTURES'
    elif market_info.get('swap', False):
        return 'SWAP'
    elif market_info.get('spot', False):
        return 'SPOT'
    else:
        return 'UNKNOWN'


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
    FUTURES_INPUT = input("Include futures markets? (y/n, default y): ").strip().lower()
    INCLUDE_FUTURES = FUTURES_INPUT != 'n'
    
    DELTA = 0.03 # 3%
    DELTA_INPUT = input("Enter minimum delta in percentage (default 3%): ")
    if DELTA_INPUT:
        DELTA = int(DELTA_INPUT) / 100.0

    CHECK_INTERVAL = 2  # 2 seconds
    CHECK_INTERVAL_INPUT = input("Enter update interval in seconds (default 2): ")
    if CHECK_INTERVAL_INPUT:
        CHECK_INTERVAL = int(CHECK_INTERVAL_INPUT)
    
    log(f'Target ticker: {TARGET_TICKER}')
    log(f'Include futures: {INCLUDE_FUTURES}')
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
    market_info_by_exchange = {}
    for ex, obj in exchange_objs.items():
        try:
            markets_by_exchange[ex] = get_target_markets(obj, TARGET_TICKER, INCLUDE_FUTURES)
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
                    
                    # Get market type information
                    market_type1 = get_market_type(market_info_by_exchange.get(ex1, {}).get(symbol, {}))
                    market_type2 = get_market_type(market_info_by_exchange.get(ex2, {}).get(symbol, {}))
                    
                    # Check arbitrage opportunity: buy on ex2, sell on ex1
                    if not (t1.get('bid') is None or t2.get('ask') is None):
                        diff = (t1.get('bid') - t2.get('ask')) / t2.get('ask')
                        if diff > DELTA:
                            volume = get_volume(t1.get('bidVolume'), t2.get('askVolume'))
                            # Add single arbitrage opportunity: buy on ex2, sell on ex1
                            results.append((symbol, market_type2, f"{ex2}", t2.get('ask'), f"{ex1}", t1.get('bid'), volume, diff))
                            # Log arbitrage opportunity to file
                            log_to_file(f"{symbol} ({market_type2}/{market_type1}) - BUY on {ex2} at {t2.get('ask')}, SELL on {ex1} at {t1.get('bid')}, Volume: {volume}, Profit: {diff*100:.2f}%")

                    # Check arbitrage opportunity: buy on ex1, sell on ex2
                    if not (t2.get('bid') is None or t1.get('ask') is None):
                        diff = (t2.get('bid') - t1.get('ask')) / t1.get('ask')
                        if diff > DELTA:
                            volume = get_volume(t2.get('bidVolume'), t1.get('askVolume'))
                            # Add single arbitrage opportunity: buy on ex1, sell on ex2
                            results.append((symbol, market_type1, f"{ex1}", t1.get('ask'), f"{ex2}", t2.get('bid'), volume, diff))
                            # Log arbitrage opportunity to file
                            log_to_file(f"{symbol} ({market_type1}/{market_type2}) - BUY on {ex1} at {t1.get('ask')}, SELL on {ex2} at {t2.get('bid')}, Volume: {volume}, Profit: {diff*100:.2f}%")
                
                # Sort results by profitability
                results.sort(key=lambda x: x[6], reverse=True)
                
                live.update(make_table())
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\nExiting gracefully...")
            sys.exit(0)


if __name__ == '__main__':
    main() 