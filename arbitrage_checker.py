import ccxt
import time
import os
from datetime import datetime
from itertools import combinations

# Настройки
EXCHANGES = ['binance', 'bybit', 'okx']
TARGET_CURRENCY = 'USDC'
CHECK_INTERVAL = 2  # секунд
DELTA = 0.03  # 3%
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
    exceptions = set()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            # Убираем комментарии и пробелы
            line = line.split('#', 1)[0].replace(' ', '').strip()
            if line:
                exceptions.add(line)
    return exceptions


def log(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{now}] {msg}')


def main():
    
    # Инициализация бирж
    exchange_objs = {}
    for ex in EXCHANGES:
        try:
            exchange_objs[ex] = getattr(ccxt, ex)()
        except Exception as e:
            log(f'Ошибка инициализации {ex}: {e}')
    
    # Получаем пары с TARGET_CURRENCY
    log(f'Загружаю пары с {TARGET_CURRENCY}...')
    markets_by_exchange = {}
    for ex, obj in exchange_objs.items():
        try:
            markets_by_exchange[ex] = get_target_markets(obj)
        except Exception as e:
            log(f'Ошибка загрузки пар {ex}: {e}')
            markets_by_exchange[ex] = set()

    # Собираем все уникальные пары
    all_pairs = set()
    for pairs in markets_by_exchange.values():
        all_pairs.update(pairs)
    # Загружаем исключения
    exceptions = load_exceptions(EXCEPTIONS_FILE)
    if exceptions:
        log(f'Исключённые пары: {sorted(exceptions)}')
    filtered_pairs = all_pairs - exceptions
    if not filtered_pairs:
        log('Нет пар для проверки после применения исключений.')
        return
    log(f'Пары для проверки: {sorted(filtered_pairs)}')

    # Предварительно вычисляем пересечения бирж для каждой пары
    pair_exchanges = {}
    for symbol in filtered_pairs:
        pair_exchanges[symbol] = [ex for ex in EXCHANGES if symbol in markets_by_exchange.get(ex, set())]

    while True:
        log('Проверка цен...')
        now_ms = int(time.time() * 1000)
        # Массово получаем тикеры для всех бирж
        tickers_by_exchange = {}
        for ex, obj in exchange_objs.items():
            try:
                tickers_by_exchange[ex] = obj.fetch_tickers(list(markets_by_exchange[ex]))
            except Exception as e:
                log(f'Ошибка массового запроса {ex}: {e}')
                tickers_by_exchange[ex] = {}
        # Для каждой пары сравниваем только между заранее найденными биржами
        for symbol in sorted(filtered_pairs):
            available_exs = pair_exchanges[symbol]
            for ex1, ex2 in combinations(available_exs, 2):
                t1 = tickers_by_exchange[ex1].get(symbol, {})
                t2 = tickers_by_exchange[ex2].get(symbol, {})
                price1 = t1.get('last')
                price2 = t2.get('last')
                ts1 = t1.get('timestamp')
                ts2 = t2.get('timestamp')
                # if (price1 is None or price2 is None or ts1 is None or ts2 is None):
                #     log(f'{symbol}: {ex1}={price1} (ts={ts1}), {ex2}={price2} (ts={ts2}) — нет данных')
                #     continue
                # if (now_ms - ts1 > MAX_AGE_MS) or (now_ms - ts2 > MAX_AGE_MS):
                #     log(f'{symbol}: {ex1}={price1} (ts={ts1}), {ex2}={price2} (ts={ts2}) — данные устарели')
                #     continue
                diff = abs(price1 - price2) / min(price1, price2)
                if diff > DELTA:
                    log(f'{symbol}: {ex1}={price1} ({ts1}), {ex2}={price2} ({ts2}), Разница={diff*100:.2f}%')
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main() 