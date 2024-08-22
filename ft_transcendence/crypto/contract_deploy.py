from solcx import compile_standard, install_solc, set_solc_version
from web3 import Web3
import json
from crypto_secreets import infura_url, private_key, deployer_account

w3 = Web3(Web3.HTTPProvider(infura_url))

with open('TournamentContractABI.json') as file:
    abi = json.load(file)

with open('TournamentContractBytecode.txt') as file:
    bytecode = file.read()

contract = w3.eth.contract(abi=abi, bytecode=bytecode)

transaction = contract.constructor().build_transaction({
    'from': deployer_account,
    'nonce': w3.eth.get_transaction_count(deployer_account),
    'gas': 3000000,  # Adjust based on contract size and complexity
    'gasPrice': w3.to_wei('20', 'gwei')
})

signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

address = tx_receipt.contractAddress
print(f"Contract deployed at address: {tx_receipt.contractAddress}")
