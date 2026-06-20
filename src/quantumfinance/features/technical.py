"""Cálculo de indicadores técnicos via pandas-ta."""

import pandas as pd
import pandas_ta as ta


def calculate_indicators(data: pd.DataFrame) -> dict:
    """Calcula RSI, MACD, médias móveis e Bandas de Bollinger a partir de um DataFrame OHLCV."""
    df = data.copy()

    df["rsi"] = ta.rsi(df["Close"], length=14)

    macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)

    df["sma_20"] = ta.sma(df["Close"], length=20)
    df["sma_50"] = ta.sma(df["Close"], length=50)
    df["ema_20"] = ta.ema(df["Close"], length=20)

    bbands = ta.bbands(df["Close"], length=20)
    df = pd.concat([df, bbands], axis=1)

    latest = df.iloc[-1]

    macd_line = latest.get("MACD_12_26_9", 0.0)
    macd_signal_line = latest.get("MACDs_12_26_9", 0.0)
    macd_signal = "bullish" if macd_line > macd_signal_line else "bearish"

    return {
        "close": round(float(latest["Close"]), 2),
        "volume": int(latest["Volume"]),
        "rsi": round(float(latest["rsi"]), 2) if pd.notna(latest["rsi"]) else 50.0,
        "macd": round(float(macd_line), 4) if pd.notna(macd_line) else 0.0,
        "macd_signal_line": round(float(macd_signal_line), 4) if pd.notna(macd_signal_line) else 0.0,
        "macd_signal": macd_signal,
        "sma_20": round(float(latest["sma_20"]), 2) if pd.notna(latest["sma_20"]) else None,
        "sma_50": round(float(latest["sma_50"]), 2) if pd.notna(latest["sma_50"]) else None,
        "ema_20": round(float(latest["ema_20"]), 2) if pd.notna(latest["ema_20"]) else None,
        "bollinger_upper": round(float(latest.get("BBU_20_2.0_2.0", 0.0)), 2) if pd.notna(latest.get("BBU_20_2.0_2.0")) else None,
        "bollinger_lower": round(float(latest.get("BBL_20_2.0_2.0", 0.0)), 2) if pd.notna(latest.get("BBL_20_2.0_2.0")) else None,
    }
