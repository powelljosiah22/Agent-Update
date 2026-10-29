#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import yfinance as yf
import pandas as pd

mcp = FastMCP("yfinance")

@mcp.tool()
def get_ticker_info(ticker: str) -> dict:
    """
    Retrieve live price, general info, and key metrics for a given ticker symbol.
    """
    try:
        t = yf.Ticker(ticker)
        return t.info
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_historical_data(ticker: str, period: str = "1mo", interval: str = "1d") -> dict:
    """
    Retrieve historical price data for a ticker.
    Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)
        hist.index = hist.index.astype(str)
        return hist.to_dict(orient="index")
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_fund_holdings(ticker: str) -> dict:
    """
    Retrieve fund holdings and top 10 holdings for ETFs or mutual funds (e.g., AVUV, AVDV, DFEV).
    """
    try:
        t = yf.Ticker(ticker)
        if hasattr(t, "funds_data") and t.funds_data is not None:
            data = {}
            if hasattr(t.funds_data, "top_holdings") and t.funds_data.top_holdings is not None:
                data["top_holdings"] = t.funds_data.top_holdings.to_dict()
            if hasattr(t.funds_data, "sector_weightings") and t.funds_data.sector_weightings is not None:
                data["sector_weightings"] = t.funds_data.sector_weightings.to_dict()
            if hasattr(t.funds_data, "asset_classes") and t.funds_data.asset_classes is not None:
                data["asset_classes"] = t.funds_data.asset_classes.to_dict()
            return data
        else:
            return {"error": f"No fund data found for {ticker}."}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_financials(ticker: str) -> dict:
    """
    Retrieve quarterly income statements, balance sheets, and cash flows.
    """
    try:
        t = yf.Ticker(ticker)
        return {
            "income_statement": t.quarterly_income_stmt.to_dict() if t.quarterly_income_stmt is not None else {},
            "balance_sheet": t.quarterly_balance_sheet.to_dict() if t.quarterly_balance_sheet is not None else {},
            "cash_flow": t.quarterly_cash_flow.to_dict() if t.quarterly_cash_flow is not None else {}
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()
