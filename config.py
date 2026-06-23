"""
Configuration file for cryptocurrency price ticker.
Contains API settings, refresh intervals, and cryptocurrency pairs.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_BASE_URL = "https://api.coingecko.com/api/v3"
API_KEY = os.getenv("COINGECKO_API_KEY", "")  # Optional: Get free API key from CoinGecko

# Default cryptocurrencies to track (symbol: name)
DEFAULT_CRYPTO_CURRENCIES = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "cardano": "ADA",
    "solana": "SOL",
    "polkadot": "DOT",
    "dogecoin": "DOGE",
    "avalanche-2": "AVAX",
    "chainlink": "LINK"
}

# Default fiat currency for price display
DEFAULT_CURRENCY = "usd"

# Refresh interval in seconds (default: 30 seconds)
REFRESH_INTERVAL = 30

# UI Configuration
WINDOW_TITLE = "Cryptocurrency Price Ticker"
WINDOW_SIZE = "600x500"

# Price change colors
COLOR_PRICE_UP = "#00ff00"  # Green
COLOR_PRICE_DOWN = "#ff0000"  # Red
COLOR_PRICE_NEUTRAL = "#ffffff"  # White

# API request timeout in seconds
API_TIMEOUT = 10

# Number of retry attempts for API calls
MAX_RETRIES = 3

# Cache duration in seconds (to avoid hitting API rate limits)
CACHE_DURATION = 5
