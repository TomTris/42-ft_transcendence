import os
import json
from django.conf import settings

# private_key=settings.PRIVATE_KEY
# infura_url=settings.INFURA_URL
# contract_address=settings.CONTRACT_ADDRESS
# deployer_account=settings.DEPLOYER_ACCOUNT
private_key='c051c92059091ba347242e96aca866a53cc31619be8a36d446c5dc0fe6551341'
infura_url='https://holesky.infura.io/v3/29c81c46168644f28a5b97385d282e11'
contract_address='0xFF5c6f0A2B78B29E28966c73f0B7E4AB93E0442E'
deployer_account='0xd2acb8D6BB9C833D1aC4d82746224AEb6bc403f8'

with open('./crypto/TournamentContractABI.json') as file:
    contract_abi = json.load(file) 