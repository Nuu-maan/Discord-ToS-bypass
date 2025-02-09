import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import random
import json
import os

import tls_client
from data.logger import NovaLogger  


NovaLogger.config(debug=True, log_file="activity.log")

BANNER = f"""
                        ████████╗ ██████╗ ███████╗    ██████╗ ██╗   ██╗██████╗  █████╗ ███████╗███████╗
                        ╚══██╔══╝██╔═══██╗██╔════╝    ██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔════╝██╔════╝
                           ██║   ██║   ██║███████╗    ██████╔╝ ╚████╔╝ ██████╔╝███████║███████╗███████╗
                           ██║   ██║   ██║╚════██║    ██╔═══╝   ╚██╔╝  ██╔══██╗██╔══██║╚════██║╚════██║
                           ██║   ╚██████╔╝███████║    ██║        ██║   ██████╔╝██║  ██║███████║███████║
                           ╚═╝    ╚═════╝ ╚══════╝    ╚═╝        ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
"""

class ConfigurationHandler:
    """Manage application configuration"""
    def __init__(self):
        self.settings = {}
        self.proxy_list = []
        self.auth_tokens = []
        
    def load_resources(self) -> None:
        """Load all external resources"""
        try:
            with open("input/config.json") as f:
                self.settings = json.load(f)
            
            self.proxy_list = self._load_proxies("input/proxies.txt")
            self.auth_tokens = self._load_tokens("input/tokens.txt")
            
            NovaLogger.event("Resources loaded", 
                            tokens=len(self.auth_tokens),
                            proxies=len(self.proxy_list),
                            threads=self.settings.get("thread_count"))
            
        except Exception as e:
            NovaLogger.fail("Configuration error", error=str(e))
            raise

    def _load_proxies(self, path: str) -> List[str]:
        """Load and normalize proxy list"""
        proxies = []
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        if not line.startswith("http"):
                            line = f"http://{line}"
                        proxies.append(line)
        return proxies

    def _load_tokens(self, path: str) -> List[str]:
        """Extract tokens from multiple formats"""
        valid_tokens = []
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        token = line.split(":")[-1]
                        valid_tokens.append(token)
        return valid_tokens


class DiscordClient:
    """Handle Discord communication layer"""
    def __init__(self, config: dict, proxies: List[str]):
        self.config = config
        self.proxy_pool = proxies
        self.browser_profile = "chrome_133"
        
    def create_session(self) -> tls_client.Session:
        """Initialize new TLS session"""
        session = tls_client.Session(
            client_identifier=self.browser_profile,
            random_tls_extension_order=True
        )
        
        session.headers = self._generate_headers()
        
        if not self.config.get("proxyless") and self.proxy_pool:
            self._apply_network_proxy(session)
            
        return session
    
    def _apply_network_proxy(self, session: tls_client.Session) -> None:
        """Configure proxy for session"""
        proxy = random.choice(self.proxy_pool)
        session.proxies = {"http": proxy, "https": proxy}

    def _generate_headers(self) -> dict:
        """Generate current browser headers"""
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Google Chrome";v="133", "Chromium";v="133", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-discord-timezone': 'Asia/Calcutta',
            'x-super-properties': self._construct_superproperties()
        }
    
    def _construct_superproperties(self) -> str:
        """Build current superproperties string"""
        return "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMy4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMzLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjM0NTY3OCwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0="


class TermsHandler:
    """Handle TOS acceptance workflow"""
    def __init__(self, config: dict, proxies: List[str]):
        self.config = config
        self.client = DiscordClient(config, proxies)
        self.stats = {"success": 0, "failed": 0, "already_member": 0, "no_access": 0, "phone_verification_required": 0}
        
    def process_tokens(self, tokens: List[str], guild_id: str) -> None:
        """Execute mass TOS acceptance"""
        NovaLogger.note("Initializing operations", 
                       target_guild=guild_id, 
                       token_count=len(tokens))
        
        with ThreadPoolExecutor(max_workers=self.config["thread_count"]) as executor:
            futures = {executor.submit(self.handle_token, token, guild_id): token 
                      for token in tokens}
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    NovaLogger.fail("Execution failure", error=str(e))

    def handle_token(self, token: str, guild_id: str) -> None:
        """Process individual token with better error categorization"""
        try:
            session = self.client.create_session()
            session.headers["authorization"] = token
            
            verification_data = self._get_verification_info(session, guild_id)
            if verification_data:
                self._submit_acceptance(session, guild_id, verification_data)
                self.stats["success"] += 1
                NovaLogger.win("Terms accepted", identifier=token[-8:])
            else:
                NovaLogger.note("No TOS required", identifier=token[-8:])
                
        except Exception as e:
            self.stats["failed"] += 1
            error_msg = str(e)
            identifier = token[-8:]
            
            if "Invalid Guild ID" in error_msg:
                NovaLogger.fail("Invalid server ID", identifier=identifier)
            elif "phone verification" in error_msg:
                self.stats["phone_verification_required"] += 1
                NovaLogger.fail("Account needs phone verification", identifier=identifier)
            elif "Missing Access" in error_msg:
                self.stats["no_access"] += 1
                NovaLogger.fail("Token lacks access to guild", identifier=identifier)
            elif "already a member" in error_msg:
                self.stats["already_member"] += 1
                NovaLogger.note("User already a member", identifier=identifier)
            else:
                NovaLogger.fail("Processing error", identifier=identifier, error=error_msg)

    def _get_verification_info(self, session: tls_client.Session, guild_id: str) -> Optional[Dict]:
        """Retrieve server verification requirements with enhanced error handling"""
        try:
            response = session.get(
                f"https://discord.com/api/v9/guilds/{guild_id}/member-verification",
                params={'with_guild': 'false'}
            )
            
            if response.status_code == 200:
                return response.json()
                
            elif response.status_code == 403:
                error_data = response.json()
                code = error_data.get('code', 0)
                if code == 10004:
                    raise Exception("Invalid Guild ID or token lacks access")
                elif code == 40002:
                    raise Exception("Account requires phone verification")
                elif code == 50001:
                    raise Exception("Missing Access")
                else:
                    raise Exception(f"Forbidden: {error_data.get('message')}")
                    
            elif response.status_code == 404:
                return None
                
            elif response.status_code == 410:
                error_data = response.json()
                if error_data.get('code') == 150009:
                    raise Exception("This user is already a member, join request is already closed")
                else:
                    raise Exception(f"Gone: {error_data.get('message')}")
                
            else:
                raise Exception(f"API Error [{response.status_code}]: {response.text}")
            
        except tls_client.exceptions.TLSClientExeption as e:
            raise Exception(f"Network failure: {str(e)}")

    def _submit_acceptance(self, session: tls_client.Session, guild_id: str, data: Dict) -> None:
        """Submit TOS acceptance to Discord"""
        payload = {
            'recommendation_id': None,
            'recommendation_context': 'GLOBAL_DISCOVERY_TOP_PICKS',
            'recommendation_outcome': 'UNKNOWN',
            **data
        }
        
        response = session.put(
            f"https://discord.com/api/v9/guilds/{guild_id}/requests/@me",
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Acceptance rejected [{response.status_code}]: {response.text}")






if __name__ == "__main__":
    print(BANNER)
    NovaLogger.config(debug=True)
    
    try:
        config_handler = ConfigurationHandler()
        config_handler.load_resources()
        
        if not config_handler.auth_tokens:
            NovaLogger.fail("No valid authentication tokens found")
            exit(1)
            
        target_guild = input("[INPUT] Guild ID: ").strip()
                    
        processor = TermsHandler(config_handler.settings, config_handler.proxy_list)
        processor.process_tokens(config_handler.auth_tokens, target_guild)
        
        
        NovaLogger.event("\nOperation Summary",
                       total=len(config_handler.auth_tokens),
                       successes=processor.stats["success"],
                       failures=processor.stats["failed"])
        
    except KeyboardInterrupt:
        NovaLogger.alert("Process terminated by user")
    except Exception as e:
        NovaLogger.alert("Critical failure", error=str(e))
    finally:
        NovaLogger.close()