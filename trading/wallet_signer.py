from web3 import Web3
from eth_account import Account
from eth_typing import ChecksumAddress
from eth_account.signers.local import LocalAccount
from typing import Optional, Dict, Any

class WalletSigner:
    def __init__(self, web3: Web3):
        self.web3 = web3
        self._account: Optional[LocalAccount] = None
        
    def load_account(self, private_key: str) -> None:
        """Load account from private key"""
        self._account = Account.from_key(private_key)
        
    def get_address(self) -> Optional[ChecksumAddress]:
        """Get wallet address"""
        if self._account:
            return self._account.address
        return None
        
    def sign_transaction(self, transaction: Dict[str, Any]) -> Optional[str]:
        """Sign transaction with loaded account"""
        if not self._account:
            print("No account loaded")
            return None
            
        try:
            # Sign transaction
            signed = self._account.sign_transaction(transaction)
            return signed.rawTransaction.hex()
            
        except Exception as e:
            print(f"Error signing transaction: {e}")
            return None 