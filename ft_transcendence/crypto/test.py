from web3 import Web3
from crypto_secreets import infura_url, private_key, contract_abi, contract_address, deployer_account
import json

web3 = Web3(Web3.HTTPProvider(infura_url))
contract = web3.eth.contract(address=contract_address, abi=contract_abi)


def get_tournaments():
    result = contract.functions.getTournaments().call()
    return result

def get_tournament_by_creator(creator_login):
    result = contract.functions.getTournamentsByCreator(creator_login).call()
    return result


def add_tournament(creator, player1, player2, player3, player4, score1_1, score1_2, score2_1, score2_2, score3_1, score3_2):
    # Build transaction
    txn = contract.functions.addTournament(creator, player1, player2, player3, player4, score1_1, score1_2, score2_1, score2_2, score3_1, score3_2).build_transaction({
        'chainId': 11155111,  # Sepolia chain ID
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei'),
        'nonce': web3.eth.get_transaction_count(deployer_account),
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=private_key)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return txn_hash

if __name__ == "__main__":
    print(get_tournaments())