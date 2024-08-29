import os
import json


# private_key = os.getenv('PRIVATE_KEY')
# infura_url = os.getenv('INFURA_URL')
# contract_address = os.getenv('CONTRACT_ADDRESS')
# deployer_account = os.getenv('DEPLOYER_ACCOUNT')

with open('./crypto/TournamentContractABI.json') as file:
    contract_abi = json.load(file) 
    
# with open('TournamentContractABI.json', 'w') as json_file:
#     json.dump(contract_abi, json_file, indent=4, sort_keys=True, ensure_ascii=False)