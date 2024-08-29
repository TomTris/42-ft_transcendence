from web3 import Web3
from .crypto_secreets import infura_url, private_key, contract_abi, contract_address, deployer_account
import json
import time
import threading

web3 = Web3(Web3.HTTPProvider(infura_url))
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

all_tournaments = []
def start_tournament_update():
    def get_tournaments_loop():
        global all_tournaments
        while True:
            all_tournaments = contract.functions.getTournaments().call()
            # print(all_tournaments)
            time.sleep(5)
    
    status_thread = threading.Thread(target=get_tournaments_loop)
    status_thread.daemon = True
    status_thread.start()

def get_tournament_by_creator(creator_login):
    result = contract.functions.getTournamentsByCreator(creator_login).call()
    return result



def add_tournament(creator, player1, player2, player3, player4, score1_1, score1_2, score2_1, score2_2, score3_1, score3_2, name='offline', online=0):
    
    scores = {
        'score1_1': score1_1,
        'score1_2': score1_2,
        'score2_1': score2_1,
        'score2_2': score2_2,
        'score3_1': score3_1,
        'score3_2': score3_2
    }

    players = {
        'player1':player1,
        'player2':player2,
        'player3':player3,
        'player4':player4
    }
    

    txn = contract.functions.addTournament(creator, name, online, players, scores).build_transaction({
        'chainId': 17000,  # Sepolia chain ID
        'gas': 1000000,
        'gasPrice': web3.eth.gas_price,
        'nonce': web3.eth.get_transaction_count(deployer_account),
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=private_key)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return txn_hash

if __name__ == "__main__":
    # add_tournament('2', 'bro', 'asd', 'sdf', 'gda', 1, 5, 5, 2, 5 ,4)
    # print(get_tournaments())
    pass