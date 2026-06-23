"""
Main price ticker application with GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import threading
import time
from datetime import datetime
from config import (
    DEFAULT_CRYPTO_CURRENCIES,
    DEFAULT_CURRENCY,
    REFRESH_INTERVAL,
    WINDOW_TITLE,
    WINDOW_SIZE,
    COLOR_PRICE_UP,
    COLOR_PRICE_DOWN,
    COLOR_PRICE_NEUTRAL
)
from api_client import CryptoAPIClient


class PriceTicker:
    """Main application class for cryptocurrency price ticker."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the price ticker application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(True, True)
        
        # API client
        self.api_client = CryptoAPIClient()
        
        # Data storage
        self.crypto_data = {}
        self.coin_ids = list(DEFAULT_CRYPTO_CURRENCIES.keys())
        self.display_names = DEFAULT_CRYPTO_CURRENCIES
        self.currency = DEFAULT_CURRENCY
        self.refresh_interval = REFRESH_INTERVAL
        
        # Refresh control
        self.is_running = True
        self.refresh_thread = None
        
        # Build UI
        self._setup_ui()
        
        # Start data refresh
        self._start_refresh_thread()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)  # Header
        main_frame.rowconfigure(1, weight=1)  # Content
        main_frame.rowconfigure(2, weight=0)  # Footer
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(
            header_frame,
            text="💰 Cryptocurrency Price Ticker",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            header_frame,
            text="🔄 Refresh",
            command=self._manual_refresh
        )
        self.refresh_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(
            header_frame,
            text="Updating...",
            font=('Arial', 9)
        )
        self.status_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Content area - Scrollable frame for price cards
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(content_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=0)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid configuration for scrollable frame
        self.scrollable_frame.columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Price cards container
        self.price_cards = {}
        self._create_price_cards()
        
        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        footer_frame.columnconfigure(0, weight=1)
        
        self.last_update_label = ttk.Label(
            footer_frame,
            text="Last update: Never",
            font=('Arial', 8)
        )
        self.last_update_label.grid(row=0, column=0, sticky=tk.W)
        
        # Currency selector
        ttk.Label(footer_frame, text="Currency:").grid(row=0, column=1, padx=(10, 5))
        self.currency_var = tk.StringVar(value=self.currency.upper())
        currency_dropdown = ttk.Combobox(
            footer_frame,
            textvariable=self.currency_var,
            values=["USD", "EUR", "GBP", "JPY", "CNY", "KRW"],
            state="readonly",
            width=6
        )
        currency_dropdown.grid(row=0, column=2)
        currency_dropdown.bind('<<ComboboxSelected>>', self._on_currency_change)
        
        # Add coin button
        self.add_btn = ttk.Button(
            footer_frame,
            text="➕ Add Coin",
            command=self._add_coin_dialog
        )
        self.add_btn.grid(row=0, column=3, padx=(10, 0))
    
    def _create_price_cards(self):
        """Create price cards for each cryptocurrency."""
        for idx, coin_id in enumerate(self.coin_ids):
            card = self._create_price_card(coin_id, idx)
            self.price_cards[coin_id] = card
    
    def _create_price_card(self, coin_id: str, row: int) -> Dict:
        """
        Create a single price card widget.
        
        Args:
            coin_id: Coin identifier
            row: Grid row position
            
        Returns:
            Dictionary containing card widgets
        """
        # Card frame with border
        card_frame = ttk.Frame(
            self.scrollable_frame,
            relief="ridge",
            borderwidth=1,
            padding="10"
        )
        card_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        card_frame.columnconfigure(0, weight=1)
        card_frame.columnconfigure(1, weight=1)
        card_frame.columnconfigure(2, weight=1)
        
        # Coin name and symbol
        name_label = ttk.Label(
            card_frame,
            text=self.display_names.get(coin_id, coin_id.upper()),
            font=('Arial', 12, 'bold')
        )
        name_label.grid(row=0, column=0, sticky=tk.W)
        
        # Price
        price_label = ttk.Label(
            card_frame,
            text="--",
            font=('Arial', 14)
        )
        price_label.grid(row=0, column=1, sticky=tk.E)
        
        # 24h change
        change_label = ttk.Label(
            card_frame,
            text="--%",
            font=('Arial', 11)
        )
        change_label.grid(row=0, column=2, sticky=tk.E, padx=(20, 0))
        
        # Market cap (subtitle)
        market_cap_label = ttk.Label(
            card_frame,
            text="",
            font=('Arial', 8),
            foreground="gray"
        )
        market_cap_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
        
        return {
            "frame": card_frame,
            "name": name_label,
            "price": price_label,
            "change": change_label,
            "market_cap": market_cap_label
        }
    
    def _update_price_cards(self):
        """Update all price cards with latest data."""
        if not self.crypto_data:
            return
        
        for coin_id, data in self.crypto_data.items():
            if coin_id not in self.price_cards:
                continue
            
            card = self.price_cards[coin_id]
            
            # Update price
            price = data.get("current_price", 0)
            if price:
                price_text = f"{self.currency.upper()} ${price:,.2f}" if price < 1000 else f"{self.currency.upper()} ${price:,.0f}"
                card["price"].config(text=price_text)
            else:
                card["price"].config(text="--")
            
            # Update 24h change
            change = data.get("price_change_percentage_24h", 0)
            if change is not None:
                change_text = f"{change:+.2f}%"
                card["change"].config(text=change_text)
                
                # Set color based on change
                if change > 0:
                    card["change"].config(foreground=COLOR_PRICE_UP)
                elif change < 0:
                    card["change"].config(foreground=COLOR_PRICE_DOWN)
                else:
                    card["change"].config(foreground=COLOR_PRICE_NEUTRAL)
            else:
                card["change"].config(text="--%", foreground=COLOR_PRICE_NEUTRAL)
            
            # Update market cap
            market_cap = data.get("market_cap", 0)
            if market_cap:
                if market_cap >= 1_000_000_000:
                    cap_text = f"Market Cap: ${market_cap / 1_000_000_000:.2f}B"
                elif market_cap >= 1_000_000:
                    cap_text = f"Market Cap: ${market_cap / 1_000_000:.2f}M"
                else:
                    cap_text = f"Market Cap: ${market_cap:,.0f}"
                card["market_cap"].config(text=cap_text)
            else:
                card["market_cap"].config(text="")
    
    def _fetch_prices(self):
        """Fetch price data from API."""
        try:
            self.status_label.config(text="Fetching data...")
            
            # Get market data
            data = self.api_client.get_coins_market_data(
                self.coin_ids,
                self.currency.lower()
            )
            
            if data:
                # Convert list to dictionary keyed by coin_id
                self.crypto_data = {item["id"]: item for item in data}
                self._update_price_cards()
                
                # Update timestamp
                now = datetime.now().strftime("%H:%M:%S")
                self.last_update_label.config(text=f"Last update: {now}")
                self.status_label.config(text="✅ Data updated")
            else:
                self.status_label.config(text="⚠️ Failed to fetch data")
                
        except Exception as e:
            print(f"Error fetching prices: {e}")
            self.status_label.config(text=f"❌ Error: {str(e)[:30]}")
    
    def _refresh_loop(self):
        """Background thread for refreshing data."""
        while self.is_running:
            # Schedule UI update in main thread
            self.root.after(0, self._fetch_prices)
            
            # Wait for next refresh
            time.sleep(self.refresh_interval)
    
    def _start_refresh_thread(self):
        """Start the background refresh thread."""
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            self.refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
            self.refresh_thread.start()
    
    def _manual_refresh(self):
        """Manually trigger a refresh."""
        self.refresh_btn.config(text="⏳ Loading...", state="disabled")
        self._fetch_prices()
        self.refresh_btn.config(text="🔄 Refresh", state="normal")
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_currency_change(self, event=None):
        """Handle currency change event."""
        self.currency = self.currency_var.get().lower()
        self._fetch_prices()
    
    def _add_coin_dialog(self):
        """Open dialog to add a new cryptocurrency."""
        # Simple dialog for adding coins
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Cryptocurrency")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Input frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Enter cryptocurrency name or symbol:").pack(anchor=tk.W)
        
        entry = ttk.Entry(main_frame, width=30)
        entry.pack(fill=tk.X, pady=(5, 10))
        entry.focus()
        
        # Info label
        info_label = ttk.Label(
            main_frame,
            text="Try: bitcoin, ethereum, cardano, solana, etc.",
            font=('Arial', 8),
            foreground="gray"
        )
        info_label.pack(anchor=tk.W)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        def add_coin():
            coin_input = entry.get().strip().lower()
            if not coin_input:
                messagebox.showwarning("Input Error", "Please enter a coin name")
                return
            
            # Show loading
            dialog.destroy()
            self.status_label.config(text=f"Adding {coin_input}...")
            
            # Check if coin exists
            try:
                # Try to get coin data
                data = self.api_client.get_coins_market_data([coin_input], self.currency.lower())
                if data and len(data) > 0:
                    # Add coin to list
                    self.coin_ids.append(coin_input)
                    self.display_names[coin_input] = coin_input.upper()
                    
                    # Create new price card
                    row = len(self.price_cards)
                    card = self._create_price_card(coin_input, row)
                    self.price_cards[coin_input] = card
                    
                    self.status_label.config(text=f"✅ Added {coin_input}")
                    self._fetch_prices()
                else:
                    messagebox.showerror("Error", f"Coin '{coin_input}' not found")
                    self.status_label.config(text="❌ Coin not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add coin: {str(e)}")
                self.status_label.config(text="❌ Failed to add coin")
        
        ttk.Button(btn_frame, text="Add Coin", command=add_coin).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
        
        # Bind Enter key
        entry.bind("<Return>", lambda e: add_coin())
    
    def _on_closing(self):
        """Handle window closing."""
        self.is_running = False
        self.api_client.clear_cache()
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = PriceTicker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
