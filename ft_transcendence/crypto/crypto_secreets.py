import os
import json

private_key='c051c92059091ba347242e96aca866a53cc31619be8a36d446c5dc0fe6551341'
infura_url='https://holesky.infura.io/v3/463414b817984c3eadaa56b5bec1a764'
contract_address='0xFF5c6f0A2B78B29E28966c73f0B7E4AB93E0442E'
deployer_account='0xd2acb8D6BB9C833D1aC4d82746224AEb6bc403f8'
# private_key = os.getenv('PRIVATE_KEY')
# infura_url = os.getenv('INFURA_URL')
# contract_address = os.getenv('CONTRACT_ADDRESS')
# deployer_account = os.getenv('DEPLOYER_ACCOUNT')

with open('./crypto/TournamentContractABI.json') as file:
    contract_abi = json.load(file) 

# with open('TournamentContractABI.json') as file:
#     contract_abi = json.load(file) 
    
# with open('TournamentContractABI.json', 'w') as json_file:
#     json.dump(contract_abi, json_file, indent=4, sort_keys=True, ensure_ascii=False)