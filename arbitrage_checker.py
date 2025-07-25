import ccxt
import time
import os
from datetime import datetime

# Настройки
EXCHANGES = ['binance', 'bybit']
TARGET_CURRENCY = 'USDC'
CHECK_INTERVAL = 2  # секунд
DELTA = 0.02  # 2%
EXCEPTIONS_FILE = 'exceptions.txt'
MAX_AGE_MS = 1000  # 1 секунда в миллисекундах


def get_target_markets(exchange):
    markets = exchange.load_markets()
    target_pairs = set()
    for symbol in markets:
        if symbol.endswith(f'/{TARGET_CURRENCY}'):
            target_pairs.add(symbol)
    return target_pairs


def load_exceptions(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def log(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{now}] {msg}')


def main():
    # Инициализация бирж
    binance = ccxt.binance()
    bybit = ccxt.bybit()

    # Получаем пары с QUOTE
    log(f'Загружаю пары с {TARGET_CURRENCY}...')
    binance_pairs = get_target_markets(binance)
    bybit_pairs = get_target_markets(bybit)
    common_pairs = binance_pairs & bybit_pairs

    # Загружаем исключения
    exceptions = load_exceptions(EXCEPTIONS_FILE)
    if exceptions:
        log(f'Исключённые пары: {sorted(exceptions)}')
    filtered_pairs = common_pairs - exceptions
    if not filtered_pairs:
        log('Нет пар для проверки после применения исключений.')
        return
    log(f'Пары для проверки: {sorted(filtered_pairs)}')

    while True:
        log('Проверка цен...')
        now_ms = int(time.time() * 1000)
        try:
            binance_tickers = binance.fetch_tickers(list(filtered_pairs))
        except Exception as e:
            log(f'Ошибка массового запроса Binance: {e}')
            binance_tickers = {}
        try:
            bybit_tickers = bybit.fetch_tickers(list(filtered_pairs))
        except Exception as e:
            log(f'Ошибка массового запроса Bybit: {e}')
            bybit_tickers = {}
        for symbol in sorted(filtered_pairs):
            try:
                binance_ticker = binance_tickers.get(symbol, {})
                bybit_ticker = bybit_tickers.get(symbol, {})
                binance_price = binance_ticker.get('last')
                bybit_price = bybit_ticker.get('last')
                binance_ts = binance_ticker.get('timestamp')
                bybit_ts = bybit_ticker.get('timestamp')
                diff = abs(binance_price - bybit_price) / min(binance_price, bybit_price)
                if diff > DELTA:
                    log(f'{symbol}: Binance={binance_price} ({binance_ts}), Bybit={bybit_price} ({bybit_ts}), Разница={diff*100:.2f}%')
            except Exception as e:
                log(f'Ошибка для {symbol}: {e}')
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main() 