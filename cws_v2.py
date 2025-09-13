# v 1.1.0 faster (async)
#!/usr/bin/env python3
import asyncio
import aiohttp
import random
import os
import time
from hdwallet import HDWallet
from hdwallet.symbols import BTC, ETH
from dataclasses import dataclass
from typing import Optional

# TESTMODE - Set to False only for authorized testing
TESTMODE = os.getenv('TESTMODE', 'true').lower() == 'true'

@dataclass
class WalletInfo:
    btc_address: str
    eth_address: str
    private_key: str
    btc_balance: float = 0.0
    eth_balance: float = 0.0

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class AsyncWalletScanner:
    def __init__(self, max_concurrent_requests: int = 10):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.scan_count = 0
        self.found_count = 0
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        connector = aiohttp.TCPConnector(limit=50, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': 'Research-Tool/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def clear_screen(self):
        """Clear the terminal screen based on the operating system."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def generate_wallet_addresses(self, private_key: str) -> WalletInfo:
        """Generate Bitcoin and Ethereum addresses from a private key - using working method."""
        hd_btc = HDWallet(BTC)
        hd_eth = HDWallet(ETH)
        
        hd_btc.from_private_key(private_key)
        hd_eth.from_private_key(private_key)
        
        return WalletInfo(
            btc_address=hd_btc.p2pkh_address(),
            eth_address=hd_eth.p2pkh_address(),
            private_key=private_key
        )

    async def get_btc_balance(self, address: str) -> float:
        """Check Bitcoin balance using blockchain API with async."""
        if TESTMODE:
            return 0.0  # Mock response in test mode
            
        async with self.semaphore:
            try:
                url = f"https://blockchain.info/balance?active={address}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[address]['final_balance'] / 100000000
            except Exception:
                pass
        return 0.0

    async def get_eth_balance(self, address: str) -> float:
        """Check Ethereum balance using etherscan API with async."""
        if TESTMODE:
            return 0.0  # Mock response in test mode
            
        async with self.semaphore:
            try:
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == '1':
                            return int(data['result']) / 10**18
            except Exception:
                pass
        return 0.0

    async def check_wallet_balances(self, wallet: WalletInfo) -> WalletInfo:
        """Check both BTC and ETH balances concurrently."""
        btc_task = asyncio.create_task(self.get_btc_balance(wallet.btc_address))
        eth_task = asyncio.create_task(self.get_eth_balance(wallet.eth_address))
        
        wallet.btc_balance, wallet.eth_balance = await asyncio.gather(btc_task, eth_task)
        return wallet

    def save_found_wallet(self, wallet: WalletInfo):
        """Save wallet with balance to file."""
        if TESTMODE:
            print(f"{Colors.GREEN}[TEST MODE] Would save wallet to file{Colors.RESET}")
            return
            
        try:
            with open('found_wallets.txt', 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] FOUND WALLET\n")
                f.write(f"BTC: {wallet.btc_address} - Balance: {wallet.btc_balance}\n")
                f.write(f"ETH: {wallet.eth_address} - Balance: {wallet.eth_balance}\n")
                f.write(f"Private Key: {wallet.private_key}\n")
                f.write("-" * 70 + "\n")
        except Exception as e:
            print(f"{Colors.RED}Error saving: {e}{Colors.RESET}")

    def display_banner(self):
        """Display the program banner."""
        mode_text = f"{Colors.GREEN}[TEST MODE - SAFE]{Colors.RESET}" if TESTMODE else f"{Colors.RED}[LIVE MODE]{Colors.RESET}"
        
        banner = f"""
    {Colors.GREEN}********************* Async Cryptocurrency Wallet Scanner ******************
    *                                                                      *
    *    Check Bitcoin and Ethereum addresses for balances (ASYNC)        *
    *    {mode_text.ljust(50)} *
    *    Generated wallets checked against blockchain APIs concurrently    *
    *    Any address with balance > 0 is saved to found_wallets.txt        *
    *                                                                      *
    ***********************************************************************{Colors.RESET}
    """
        print(banner)

    def display_results(self, wallet: WalletInfo):
        """Display scan results in the original style."""
        self.clear_screen()
        self.display_banner()
        
        print(f"{Colors.RED}{'='*24}[{Colors.WHITE}Scan:{Colors.YELLOW} {self.scan_count:,} "
              f"{Colors.WHITE}Found:{Colors.GREEN} {self.found_count}{Colors.RED}]{'='*24}{Colors.RESET}")
        
        btc_color = Colors.GREEN if wallet.btc_balance > 0 else Colors.YELLOW
        eth_color = Colors.GREEN if wallet.eth_balance > 0 else Colors.YELLOW
        
        print(f"        | BTC Address {Colors.RED}(P2PKH) {Colors.RESET} | "
              f"BAL: {btc_color}{wallet.btc_balance:.8f}{Colors.RESET} | {Colors.WHITE}{wallet.btc_address}{Colors.RESET}")
        
        print(f"        | ETH Address {Colors.RED}(ETH)   {Colors.RESET} | "
              f"BAL: {eth_color}{wallet.eth_balance:.8f}{Colors.RESET} | {Colors.WHITE}{wallet.eth_address}{Colors.RESET}")
        
        print(f"        | Private Key {Colors.RED}(HEX)   {Colors.RESET} | {Colors.RED}{wallet.private_key}{Colors.RESET}")
        print(f"        {Colors.RED}{'='*70}{Colors.RESET}")
        
        if wallet.btc_balance > 0 or wallet.eth_balance > 0:
            print(f"{Colors.GREEN}*** WALLET WITH BALANCE FOUND! ***{Colors.RESET}")

    async def run_scan(self):
        """Main scanning loop - async version of your working code."""
        try:
            while True:
                # Generate a random private key (same method as original)
                private_key = "".join(random.choice("0123456789abcdef") for _ in range(64))
                
                # Generate wallet addresses using your working method
                wallet = self.generate_wallet_addresses(private_key)
                
                # Check balances concurrently (this is the async improvement)
                wallet = await self.check_wallet_balances(wallet)
                
                self.scan_count += 1
                
                # Save if balance found
                if wallet.btc_balance > 0 or wallet.eth_balance > 0:
                    self.found_count += 1
                    self.save_found_wallet(wallet)
                
                # Display results in original format
                self.display_results(wallet)
                
                # Small delay to avoid overwhelming APIs (reduced from 1 second)
                if not TESTMODE:
                    await asyncio.sleep(0.3)
                else:
                    await asyncio.sleep(0.1)  # Faster in test mode
                    
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Scan interrupted by user. Total scanned: {self.scan_count:,}, Found: {self.found_count}{Colors.RESET}")

async def main():
    """Main entry point."""
    if TESTMODE:
        print(f"{Colors.GREEN}✓ Running in TEST MODE - Mock responses, no live API calls{Colors.RESET}")
    else:
        print(f"{Colors.RED}⚠ LIVE MODE - Real blockchain API calls enabled{Colors.RESET}")
    
    time.sleep(1)
    
    async with AsyncWalletScanner(max_concurrent_requests=10) as scanner:
        await scanner.run_scan()

def set_testmode():
    """Handle TESTMODE setting for Windows users."""
    global TESTMODE
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['live', 'false', 'real']:
            TESTMODE = False
            print(f"{Colors.RED}TESTMODE disabled via argument{Colors.RESET}")
        elif arg in ['test', 'true', 'safe']:
            TESTMODE = True
            print(f"{Colors.GREEN}TESTMODE enabled via argument{Colors.RESET}")

if __name__ == "__main__":
    try:
        set_testmode()
        print("Starting async scanner...")
        time.sleep(1)
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Program terminated by user{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.RESET}")
        exit(1)
