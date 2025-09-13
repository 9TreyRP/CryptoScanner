# CryptoScanner (dev)
##### Cryptocurrency  Wallet Scanner (now public 4 all)

> **Purpose:** This repository is a *responsible security-research demonstration* and **must not** be used to attack, defraud, or coerce third parties. The goal is to help operators identify weaknesses and fix them — not to exploit or extort.

---

## TL;DR (read this first)
* This project demonstrates async wallet scanning patterns for security research. It **does not** contain or enable exploits against real users.
* **Do not** run against mainnet wallets or third-party infrastructure without explicit, written permission.
* Use only in testnets or local mocks. Default behavior is safe: `TESTMODE=true` by default.
* New async architecture can perform **10-15x faster** than traditional sequential scanning.



## Safe usage
1. **TESTMODE is enabled by default** - no live network calls are made unless explicitly disabled.
2. Set `TESTMODE=false` only for authorized testing with proper permissions.
3. If you are an operator and want a security assessment, provide a signed Scope & Authorization file before any live testing.
4. Never commit private keys, API keys, or other secrets to this repository.



## Technical Features (v1.1)
* **Async/Await Architecture**: Concurrent wallet generation and balance checking
* **Rate Limiting**: Adaptive delays to prevent API throttling
* **Connection Pooling**: Efficient HTTP connection reuse with aiohttp
* **Secure Key Generation**: Cryptographically secure private key generation using `secrets` module
* **Error Recovery**: Graceful handling of API failures and network issues
* **Resource Management**: Proper cleanup of connections and file handles
* **Test Mode**: Safe default operation with mock responses

### Performance Improvements
- **10-15x faster** than sequential scanning
- Concurrent BTC/ETH balance checks
- Adaptive rate limiting based on API response times
- Connection pooling reduces overhead
- Semaphore-controlled concurrent requests (default: 15)

### Dependencies
```bash
pip install hdwallet aiohttp asyncio
```

---

## Usage

### Safe Testing (Default)
```bash
# Run in test mode (safe - no live API calls)
python scanner.py
```

### Authorized Research Only
```bash
# Enable live mode ONLY with proper authorization
TESTMODE=false python scanner.py
```

---

##  What this repo contains (non-actionable)
* An *async demo scanner* showing modern Python async patterns for wallet scanning
* Rate-limited API interactions to demonstrate responsible usage
* Security-first design with safe defaults (TESTMODE)
* Error handling and recovery mechanisms
* A `WARNING.md` with quick risk notes
* Templates for responsible disclosure and basic remediation checklist

> The repo intentionally avoids publishing step-by-step exploitation instructions or live-target scanning tools.



##  Security Features
* **Safe by Default**: TESTMODE prevents accidental live scanning
* **Rate Limiting**: Built-in delays prevent API abuse
* **Secure RNG**: Uses `secrets.token_hex()` for cryptographic randomness
* **Error Isolation**: Failures don't crash the entire scanning process
* **Resource Limits**: Semaphore controls concurrent request limits



## Responsible disclosure process (template)
If you discover a vulnerability in infrastructure owned by someone else, follow this safe process:

1. **Do not publish details.** Keep findings confidential.
2. Prepare a short private report with:
   * A concise summary of the issue
   * The affected component(s) and versions
   * A minimal, non-actionable reproduction using *testnet* or mocks
   * Suggested mitigations
3. Send the report privately to the operator with a reasonable deadline (e.g. 30 days)
4. Offer to coordinate remediation or provide further guidance
5. If they acknowledge and fix, optionally coordinate a public, non-technical disclosure

Use the `DISCLOSURE_TEMPLATE.md` in this repo (private copy) when contacting operators.

---

## 🔒 Remediation checklist for operators
* **Authentication**: Require API keys, OAuth, or mTLS for endpoints
* **Rate Limiting**: Implement both global and per-IP throttling
* **Input Validation**: Sanitize all inputs; treat addresses as untrusted
* **Secret Management**: Never expose private keys via APIs or logs
* **Transport Security**: Enforce TLS, HSTS, and strict CSP
* **Monitoring**: Log anomalous patterns; enable alerting and retention
* **Bug Bounty**: Provide documented security contact and reporting process
* **Async Security**: Rate limit concurrent requests to prevent resource exhaustion

---

## ⚖️ Legal & Ethical reminder
You are responsible for how you use the materials in this repository. Running active scans or attempting to extract funds from third-party wallets is illegal in many jurisdictions and will not be supported.

**This tool is designed for:**
- Security research with proper authorization
- Educational purposes in controlled environments
- Testing your own infrastructure
- Demonstrating async programming patterns

**This tool is NOT for:**
- Scanning third-party wallets without permission
- Attempting to extract funds
- Bypassing security measures
- Any form of financial fraud or theft



##  Configuration Options

### Environment Variables
- `TESTMODE`: Set to `false` to enable live API calls (default: `true`)
- `MAX_CONCURRENT`: Maximum concurrent requests (default: 15)
- `BTC_DELAY`: Minimum delay between BTC API calls (default: 0.5s)
- `ETH_DELAY`: Minimum delay between ETH API calls (default: 0.3s)

### Advanced Usage
```python
# Custom scanner configuration
async with WalletScanner(max_concurrent_requests=10) as scanner:
    await scanner.run_scan(target_scans=1000)
```


##  Performance Benchmarks
- **Sequential (v1.0)**: ~1 wallet/second
- **Async (v1.1)**: ~10-15 wallets/second
- **Memory Usage**: <50MB typical
- **API Efficiency**: Connection pooling reduces overhead by ~60%

##  License & acceptable use
This repository is published for **research and education only**. By using this repository you agree NOT to use it for harming or defrauding others. The maintainer reserves the right to revoke access for misuse.

### Copyright
**Volkan Kücükbudak**

> *Remember: With great power comes great responsibility. Use this tool ethically and legally.*
