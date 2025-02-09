# Discord Guild TOS Mass Accepter

## Overview
This script automates the process of accepting Terms of Service (TOS) for multiple Discord guilds using `tls_client`. It supports multi-threading, proxies, and structured logging for efficient and scalable execution.

## Features
- **Automated TOS Acceptance**: Accepts Discord server TOS for multiple tokens.
- **Multi-Threading**: Executes requests in parallel for faster processing.
- **Proxy Support**: Uses proxies to avoid rate limiting.
- **Custom Headers & TLS Spoofing**: Uses `tls_client` to bypass fingerprinting.
- **Logging with NovaLogger**: Structured event logging for easy debugging.
- **Efficient Error Handling**: Handles various errors such as invalid tokens, rate limits, and failed requests.

## Requirements
- Python 3.8+
- `tls_client`
- `requests`
- `concurrent.futures`
- `json`

## Installation
```sh
pip install tls_client requests
```

## Configuration
Edit `config.json` with your settings:
```json
{
    "thread_count": 50,
    "proxyless": true,
    "max_retries": 3,
    "request_timeout": 15,
    "debug_mode": true,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}```

## Usage
Run the script with:
```sh
python script.py
```

## Notes
- Ensure tokens are valid and have permission to accept TOS.
- Proxies help prevent rate limiting but should be high-quality.
- Multi-threading speeds up processing but may increase the chance of rate limits.

## Disclaimer
This script is for educational purposes only. Use responsibly and comply with Discord's Terms of Service.

