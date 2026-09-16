import random
from flask import Flask, jsonify, render_template

try:
  import MetaTrader5 as mt5

  MT5_AVAILABLE = True
except ImportError:
  MT5_AVAILABLE = False

app = Flask(__name__, template_folder='templates')

# Mock base prices for cloud/Codespaces preview mode
mock_prices = {
    'XAUUSD': 2658.0,
    'NAS100': 18450.0,
    'US30': 39100.0,
    'SPX500': 5200.0,
    'Vol 75': 451200.0,
    'Vol 100': 891200.0,
}


def init_mt5():
  if not MT5_AVAILABLE:
    return False
  try:
    if mt5.initialize():
      return True
  except:
    pass
  return False


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/api/candles/<symbol>/<tf>')
def get_candles(symbol, tf):
  candles = []
  base_price = mock_prices.get(symbol, 2658.0)

  if init_mt5():
    broker_symbol = symbol
    if symbol == 'Vol 75':
      broker_symbol = 'Volatility 75 Index'
    elif symbol == 'Vol 100':
      broker_symbol = 'Volatility 100 Index'

    tf_map = {
        '1H': mt5.TIMEFRAME_H1,
        '15m': mt5.TIMEFRAME_M15,
        '5m': mt5.TIMEFRAME_M5,
    }
    mt5_tf = tf_map.get(tf, mt5.TIMEFRAME_H1)
    rates = mt5.copy_rates_from_pos(broker_symbol, mt5_tf, 0, 85)
    if rates is not None:
      for r in rates:
        candles.append({
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'close': float(r['close']),
        })
      return jsonify(candles)

  # Cloud / Codespaces Mock Candle Generator
  curr = base_price
  for i in range(85):
    open_p = curr
    change = (random.random() - 0.51) * (base_price * 0.0015)
    close_p = open_p + change
    high_p = max(open_p, close_p) + random.random() * (base_price * 0.0008)
    low_p = min(open_p, close_p) - random.random() * (base_price * 0.0008)
    candles.append({
        'open': round(open_p, 2),
        'high': round(high_p, 2),
        'low': round(low_p, 2),
        'close': round(close_p, 2),
    })
    curr = close_p
  return jsonify(candles)


@app.route('/api/ticker/<symbol>')
def get_ticker(symbol):
  base_price = mock_prices.get(symbol, 2658.0)
  if init_mt5():
    broker_symbol = symbol
    if symbol == 'Vol 75':
      broker_symbol = 'Volatility 75 Index'
    elif symbol == 'Vol 100':
      broker_symbol = 'Volatility 100 Index'
    tick = mt5.symbol_info_tick(broker_symbol)
    if tick:
      return jsonify(
          {'symbol': symbol, 'price': round(float(tick.bid), 2), 'bias': 'MT5'}
      )

  # Live tick jitter for cloud preview
  jitter = (random.random() - 0.49) * (base_price * 0.0004)
  mock_prices[symbol] = base_price + jitter
  return jsonify({
      'symbol': symbol,
      'price': round(mock_prices[symbol], 2),
      'bias': 'Synced (Cloud)',
  })


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)