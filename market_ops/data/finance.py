from typing import Dict, Any
import yfinance as yf


def fetch_yahoo(symbols: list) -> Dict[str, Any]:
    """Fetch latest price and percent change for a list of symbols using yfinance."""
    if not symbols:
        return {}
    data: Dict[str, Any] = {}
    unique_symbols = [s for s in dict.fromkeys(symbols) if s]
    for sym in unique_symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                last = hist["Close"][-1]
                prev = hist["Close"][-2]
                change = (last - prev) / prev * 100
            else:
                last = hist["Close"][-1] if len(hist) else 0.0
                change = 0.0
            data[sym] = {"price": float(last), "change": float(change)}
        except Exception as e:
            data[sym] = {"price": None, "change": None, "error": str(e)}
    return data
