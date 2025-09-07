#!/usr/bin/env python3
"""
Seed script to add basic trading instruments to the database.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.database.session import SessionLocal
from src.models.instruments import Instrument


def seed_instruments():
    """Add basic trading instruments to the database."""

    # Basic forex pairs
    forex_pairs = [
        {
            "symbol": "EURUSD",
            "name": "Euro/US Dollar",
            "type": "FOREX",
            "base_currency": "EUR",
            "quote_currency": "USD",
        },
        {
            "symbol": "GBPUSD",
            "name": "British Pound/US Dollar",
            "type": "FOREX",
            "base_currency": "GBP",
            "quote_currency": "USD",
        },
        {
            "symbol": "USDJPY",
            "name": "US Dollar/Japanese Yen",
            "type": "FOREX",
            "base_currency": "USD",
            "quote_currency": "JPY",
        },
        {
            "symbol": "USDCAD",
            "name": "US Dollar/Canadian Dollar",
            "type": "FOREX",
            "base_currency": "USD",
            "quote_currency": "CAD",
        },
        {
            "symbol": "AUDUSD",
            "name": "Australian Dollar/US Dollar",
            "type": "FOREX",
            "base_currency": "AUD",
            "quote_currency": "USD",
        },
        {
            "symbol": "NZDUSD",
            "name": "New Zealand Dollar/US Dollar",
            "type": "FOREX",
            "base_currency": "NZD",
            "quote_currency": "USD",
        },
        {
            "symbol": "USDCHF",
            "name": "US Dollar/Swiss Franc",
            "type": "FOREX",
            "base_currency": "USD",
            "quote_currency": "CHF",
        },
    ]

    # Crypto pairs
    crypto_pairs = [
        {
            "symbol": "BTCUSD",
            "name": "Bitcoin/US Dollar",
            "type": "CRYPTO",
            "base_currency": "BTC",
            "quote_currency": "USD",
        },
        {
            "symbol": "ETHUSD",
            "name": "Ethereum/US Dollar",
            "type": "CRYPTO",
            "base_currency": "ETH",
            "quote_currency": "USD",
        },
        {
            "symbol": "XRPUSD",
            "name": "Ripple/US Dollar",
            "type": "CRYPTO",
            "base_currency": "XRP",
            "quote_currency": "USD",
        },
    ]

    # Commodities
    commodities = [
        {
            "symbol": "XAUUSD",
            "name": "Gold/US Dollar",
            "type": "COMMODITY",
            "base_currency": "XAU",
            "quote_currency": "USD",
        },
        {
            "symbol": "XAGUSD",
            "name": "Silver/US Dollar",
            "type": "COMMODITY",
            "base_currency": "XAG",
            "quote_currency": "USD",
        },
    ]

    # Indices
    indices = [
        {
            "symbol": "SPX500",
            "name": "S&P 500",
            "type": "INDEX",
            "base_currency": "SPX",
            "quote_currency": "USD",
        },
        {
            "symbol": "NAS100",
            "name": "NASDAQ 100",
            "type": "INDEX",
            "base_currency": "NAS",
            "quote_currency": "USD",
        },
        {
            "symbol": "GER30",
            "name": "DAX 30",
            "type": "INDEX",
            "base_currency": "GER",
            "quote_currency": "EUR",
        },
    ]

    all_instruments = forex_pairs + crypto_pairs + commodities + indices

    db = SessionLocal()
    try:
        for instrument_data in all_instruments:
            # Check if instrument already exists
            existing = (
                db.query(Instrument)
                .filter(Instrument.symbol == instrument_data["symbol"])
                .first()
            )
            if not existing:
                instrument = Instrument(**instrument_data)
                db.add(instrument)
                print(f"Added instrument: {instrument_data['symbol']}")
            else:
                print(f"Instrument already exists: {instrument_data['symbol']}")

        db.commit()
        print(f"Successfully seeded {len(all_instruments)} instruments")

    except Exception as e:
        print(f"Error seeding instruments: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_instruments()
