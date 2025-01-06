from web3 import Web3
from eth_typing import ChecksumAddress
from typing import Optional

class WalletBalance:
    def __init__(self, web3: Web3):
        self.web3 = web3
        
    def check_eth_balance(self, address: ChecksumAddress) -> float:
        """Check ETH balance for given address"""
        balance_wei = self.web3.eth.get_balance(address)
        return self.web3.from_wei(balance_wei, 'ether')
        
    def check_token_balance(self, token_address: ChecksumAddress, wallet_address: ChecksumAddress) -> Optional[float]:
        """Check token balance for given address"""
        try:
            # Get token contract
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=[{
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }]
            )
            
            # Get balance
            balance = token_contract.functions.balanceOf(wallet_address).call()
            return float(balance) / (10 ** 18)  # Assuming 18 decimals
            
        except Exception as e:
            print(f"Error checking token balance: {e}")
            return None 