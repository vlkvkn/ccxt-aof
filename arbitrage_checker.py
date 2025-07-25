import ccxt
import time

# Настройки
EXCHANGES = ['binance', 'bybit']
QUOTE = 'USDT'
CHECK_INTERVAL = 10  # секунд
THRESHOLD = 0.02  # 2%


def get_usdt_markets(exchange):
    markets = exchange.load_markets()
    usdt_pairs = set()
    for symbol in markets:
        if symbol.endswith(f'/{QUOTE}'):
            usdt_pairs.add(symbol)
    return usdt_pairs


def main():
    # Инициализация бирж
    binance = ccxt.binance()
    bybit = ccxt.bybit()

    # Получаем пары с USDT
    print('Загружаю пары с USDT...')
    binance_pairs = get_usdt_markets(binance)
    bybit_pairs = get_usdt_markets(bybit)
    common_pairs = binance_pairs & bybit_pairs
    if not common_pairs:
        print('Нет общих пар с USDT между Binance и Bybit.')
        return
    print(f'Общие пары: {sorted(common_pairs)}')

    while True:
        print('\nПроверка цен...')
        for symbol in sorted(common_pairs):
            try:
                binance_ticker = binance.fetch_ticker(symbol)
                bybit_ticker = bybit.fetch_ticker(symbol)
                binance_price = binance_ticker['last']
                bybit_price = bybit_ticker['last']
                if binance_price and bybit_price:
                    diff = abs(binance_price - bybit_price) / min(binance_price, bybit_price)
                    if diff > THRESHOLD:
                        print(f'{symbol}: Binance={binance_price}, Bybit={bybit_price}, Разница={diff*100:.2f}%')
            except Exception as e:
                print(f'Ошибка для {symbol}: {e}')
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main() 