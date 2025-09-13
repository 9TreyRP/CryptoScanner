#!/usr/bin/env python3
import asyncio
import aiohttp
import secrets
import os
import time
from concurrent.futures import ThreadPoolExecutor
from hdwallet import HDWallet
from hdwallet.symbols import BTC, ETH
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

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

class WalletScanner:
    def __init__(self, max_concurrent_requests: int = 10):
        self.session: Optional[aiohttp.ClientSession] = None
        self.max_concurrent = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.scan_count = 0
        self.found_count = 0
        self.request_delays = {'btc': 0.5, 'eth': 0.3}  # Rate limiting
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        connector = aiohttp.TCPConnector(limit=self.max_concurrent, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': 'Research-Tool/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def generate_secure_private_key(self) -> str:
        """Generate cryptographically secure private key"""
        if TESTMODE:
            # Use deterministic keys for testing
            return f"{'0' * 63}{self.scan_count % 10}"
        return secrets.token_hex(32)

    def generate_wallet_addresses(self, private_key: str) -> WalletInfo:
        """Generate wallet addresses from private key with error handling"""
        try:
            hd_btc = HDWallet(BTC)
            hd_eth = HDWallet(ETH)
            
            hd_btc.from_private_key(private_key)
            hd_eth.from_private_key(private_key)
            
            return WalletInfo(
                btc_address=hd_btc.p2pkh_address(),
                eth_address=hd_eth.p2pkh_address(),
                private_key=private_key
            )
        except Exception as e:
            print(f"{Colors.RED}Error generating wallet: {e}{Colors.RESET}")
            raise

    async def get_btc_balance(self, address: str) -> float:
        """Get Bitcoin balance with rate limiting and error handling"""
        if TESTMODE:
            return 0.0  # Mock response for testing
            
        async with self.semaphore:
            try:
                await asyncio.sleep(self.request_delays['btc'])
                url = f"https://blockchain.info/balance?active={address}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get(address, {}).get('final_balance', 0) / 100000000
                    elif response.status == 429:  # Rate limited
                        self.request_delays['btc'] *= 1.5  # Increase delay
                        await asyncio.sleep(2)
                        
            except Exception as e:
                if not TESTMODE:
                    print(f"{Colors.YELLOW}BTC API error: {str(e)[:50]}...{Colors.RESET}")
                
        return 0.0

    async def get_eth_balance(self, address: str) -> float:
        """Get Ethereum balance with rate limiting and error handling"""
        if TESTMODE:
            return 0.0  # Mock response for testing
            
        async with self.semaphore:
            try:
                await asyncio.sleep(self.request_delays['eth'])
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == '1':
                            return int(data.get('result', 0)) / 10**18
                    elif response.status == 429:  # Rate limited
                        self.request_delays['eth'] *= 1.5
                        await asyncio.sleep(2)
                        
            except Exception as e:
                if not TESTMODE:
                    print(f"{Colors.YELLOW}ETH API error: {str(e)[:50]}...{Colors.RESET}")
                
        return 0.0

    async def check_wallet(self, wallet: WalletInfo) -> WalletInfo:
        """Check wallet balances concurrently"""
        btc_task = asyncio.create_task(self.get_btc_balance(wallet.btc_address))
        eth_task = asyncio.create_task(self.get_eth_balance(wallet.eth_address))
        
        wallet.btc_balance, wallet.eth_balance = await asyncio.gather(
            btc_task, eth_task, return_exceptions=False
        )
        
        return wallet

    def save_found_wallet(self, wallet: WalletInfo) -> None:
        """Save wallet with balance to file"""
        if TESTMODE:
            return  # Don't save in test mode
            
        try:
            with open('found_wallets.txt', 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] FOUND WALLET\n")
                f.write(f"BTC: {wallet.btc_address} - Balance: {wallet.btc_balance:.8f}\n")
                f.write(f"ETH: {wallet.eth_address} - Balance: {wallet.eth_balance:.8f}\n")
                f.write(f"Private Key: {wallet.private_key}\n")
                f.write("-" * 70 + "\n")
        except IOError as e:
            print(f"{Colors.RED}Error saving wallet: {e}{Colors.RESET}")

    def display_banner(self) -> None:
        """Display program banner with test mode warning"""
        mode_text = f"{Colors.YELLOW}[TEST MODE - SAFE]{Colors.RESET}" if TESTMODE else f"{Colors.RED}[LIVE MODE - USE RESPONSIBLY]{Colors.RESET}"
        
        banner = f"""
{Colors.GREEN}********************* Cryptocurrency Wallet Scanner v1.1 *********************
*                                                                      *
*    Optimized async scanner for Bitcoin and Ethereum wallets         *
*    {mode_text.ljust(50)} *
*    {hdwallet_status.ljust(50)} *
*    Rate-limited requests with concurrent processing                  *
*                                                                      *
***********************************************************************{Colors.RESET}
"""
        print(banner)

    def display_results(self, wallet: WalletInfo) -> None:
        """Display scan results"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.display_banner()
        
        print(f"{Colors.RED}{'='*22}[{Colors.WHITE}Scanned:{Colors.YELLOW} {self.scan_count:,} "
              f"{Colors.WHITE}Found:{Colors.GREEN} {self.found_count}{Colors.RED}]{'='*22}{Colors.RESET}")
        
        btc_color = Colors.GREEN if wallet.btc_balance > 0 else Colors.WHITE
        eth_color = Colors.GREEN if wallet.eth_balance > 0 else Colors.WHITE
        
        print(f"  | BTC {Colors.BLUE}P2PKH{Colors.RESET} | "
              f"BAL: {btc_color}{wallet.btc_balance:.8f}{Colors.RESET} | {wallet.btc_address}")
        
        print(f"  | ETH {Colors.BLUE}Addr {Colors.RESET} | "
              f"BAL: {eth_color}{wallet.eth_balance:.8f}{Colors.RESET} | {wallet.eth_address}")
        
        print(f"  | Private Key | {Colors.RED}{wallet.private_key}{Colors.RESET}")
        print(f"  {Colors.RED}{'='*75}{Colors.RESET}")
        
        if wallet.btc_balance > 0 or wallet.eth_balance > 0:
            print(f"{Colors.GREEN}*** WALLET WITH BALANCE FOUND! ***{Colors.RESET}")

    async def run_scan(self, target_scans: Optional[int] = None) -> None:
        """Main scanning loop"""
        try:
            while target_scans is None or self.scan_count < target_scans:
                # Generate wallet
                private_key = self.generate_secure_private_key()
                wallet = self.generate_wallet_addresses(private_key)
                
                # Check balances
                wallet = await self.check_wallet(wallet)
                
                self.scan_count += 1
                
                # Save if balance found
                if wallet.btc_balance > 0 or wallet.eth_balance > 0:
                    self.found_count += 1
                    self.save_found_wallet(wallet)
                
                # Display results
                self.display_results(wallet)
                
                # Adaptive delay based on API response times
                if not TESTMODE:
                    base_delay = max(self.request_delays.values())
                    await asyncio.sleep(min(base_delay * 0.5, 0.1))  # Minimum delay
                    
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Scan interrupted. Total: {self.scan_count:,}, Found: {self.found_count}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Scan error: {e}{Colors.RESET}")

async def main():
    """Main entry point"""
    if TESTMODE:
        print(f"{Colors.GREEN}✓ Running in TEST MODE - Safe mock addresses only{Colors.RESET}")
    else:
        print(f"{Colors.RED}⚠ LIVE MODE - Real API calls enabled{Colors.RESET}")
    
    time.sleep(1)
    
    async with WalletScanner(max_concurrent_requests=15) as scanner:
        await scanner.run_scan()

# Windows PowerShell environment variable handling
def set_testmode():
    """Handle TESTMODE setting for Windows"""
    global TESTMODE
    
    # Check command line args for Windows users
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['live', 'false', 'real']:
            TESTMODE = False
            print(f"{Colors.RED}TESTMODE disabled via command line argument{Colors.RESET}")
        elif sys.argv[1].lower() in ['test', 'true', 'safe']:
            TESTMODE = True
            print(f"{Colors.GREEN}TESTMODE enabled via command line argument{Colors.RESET}")

if __name__ == "__main__":
    try:
        set_testmode()
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Program terminated by user{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.RESET}")
        exit(1)
