import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mt5_connection():
    print("Testing MT5 Connection...")
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return False
    
    # Get MT5 credentials from environment
    login = int(os.getenv('MT5_LOGIN', '274056656'))
    password = os.getenv('MT5_PASSWORD', 'Raimucok123@')
    server = os.getenv('MT5_SERVER', 'Exness-MT5Trial6')
    
    print(f"\nAttempting to connect to {server} with account {login}")
    
    # Try to login
    if not mt5.login(login=login, password=password, server=server):
        print(f"Login failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    print("\nMT5 Connection successful!")
    print(f"Account info: {mt5.account_info()._asdict()}")
    print(f"\nSymbols available: {mt5.symbols_total()}")
    
    # Test getting some basic market data
    eurusd_info = mt5.symbol_info("EURUSD")
    if eurusd_info is not None:
        print("\nEURUSD Info:")
        print(f"Bid: {eurusd_info.bid}")
        print(f"Ask: {eurusd_info.ask}")
        print(f"Spread: {eurusd_info.spread} points")
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    test_mt5_connection()
