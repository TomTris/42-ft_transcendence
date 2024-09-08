import os
import json
from django.conf import settings

private_key=settings.PRIVATE_KEY
infura_url=settings.INFURA_URL
contract_address=settings.CONTRACT_ADDRESS
deployer_account=settings.DEPLOYER_ACCOUNT

with open('./crypto/TournamentContractABI.json') as file:
    contract_abi = json.load(file) 
