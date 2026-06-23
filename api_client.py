"""
API client for fetching cryptocurrency price data from CoinGecko.
Handles rate limiting, retries, and error handling.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from config import API_BASE_URL, API_KEY, API_TIMEOUT, MAX_RETRIES, CACHE_DURATION


class CryptoAPIClient:
    """Client for interacting with CoinGecko API."""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.api_key = API_KEY
        self.timeout = API_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.cache = {}
        self.cache_duration = CACHE_DURATION
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make an API request with rate limiting and retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters for the request
            
        Returns:
            JSON response as dictionary or None if failed
        """
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        # Add API key if available
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        
        # Cache key based on endpoint and params
        cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        
        # Check cache
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if current_time - cache_time < self.cache_duration:
                return cache_data
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    # Cache the response
                    self.cache[cache_key] = (current_time, data)
                    return data
                elif response.status_code == 429:
                    # Rate limit exceeded - wait and retry
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"API error: {response.status_code} - {response.text}")
                    if attempt == self.max_retries - 1:
                        return None
                    time.sleep(1)
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
        
        return None
    
    def get_simple_price(self, coin_ids: List[str], vs_currency: str = "usd") -> Optional[Dict]:
        """
        Get current price for multiple cryptocurrencies.
        
        Args:
            coin_ids: List of coin IDs (e.g., ['bitcoin', 'ethereum'])
            vs_currency: Currency to display prices in (e.g., 'usd')
            
        Returns:
            Dictionary with price data or None if failed
        """
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_change": "true",
            "include_24hr_vol": "true"
        }
        
        return self._make_request("simple/price", params)
    
    def get_coins_market_data(self, coin_ids: List[str], vs_currency: str = "usd") -> Optional[List[Dict]]:
        """
        Get detailed market data for cryptocurrencies.
        
        Args:
            coin_ids: List of coin IDs
            vs_currency: Currency to display prices in
            
        Returns:
            List of coin market data dictionaries or None if failed
        """
        params = {
            "vs_currency": vs_currency,
            "ids": ",".join(coin_ids),
            "order": "market_cap_desc",
            "per_page": len(coin_ids),
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        
        return self._make_request("coins/markets", params)
    
    def get_coin_history(self, coin_id: str, days: int = 1) -> Optional[Dict]:
        """
        Get historical price data for a coin.
        
        Args:
            coin_id: Coin ID (e.g., 'bitcoin')
            days: Number of days of historical data
            
        Returns:
            Historical data dictionary or None if failed
        """
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        return self._make_request(f"coins/{coin_id}/market_chart", params)
    
    def clear_cache(self):
        """Clear the API response cache."""
        self.cache.clear()
    
    def get_supported_currencies(self) -> Optional[List[str]]:
        """Get list of supported fiat currencies."""
        return self._make_request("simple/supported_vs_currencies")
