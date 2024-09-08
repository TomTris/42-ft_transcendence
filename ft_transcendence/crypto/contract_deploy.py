from web3 import Web3
import json
from .crypto_secreets import infura_url, private_key, deployer_account

w3 = Web3(Web3.HTTPProvider(infura_url))

with open('TournamentContractABI.json') as file:
    abi = json.load(file)

with open('TournamentContractBytecode.txt') as file:
    bytecode = file.read()

# 1327800

def deploy_contract():
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    transaction = contract.constructor().build_transaction({
        'from': deployer_account,
        'nonce':  w3.eth.get_transaction_count(deployer_account),  # Ensure this is after the cancel transaction
        'gas': 1408762,  # Adjust based on contract size and complexity
        'gasPrice': w3.eth.gas_price  # Ensure this is set appropriately
    })

    try:
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        # print(f'Deploy transaction hash: {w3.to_hex(tx_hash)}')

        # Wait for the transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        # print(f"Contract deployed at address: {tx_receipt.contractAddress}")
    except Exception as e:
        # print(f'Error deploying contract: {e}')

deploy_contract()


