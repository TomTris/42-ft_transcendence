from brownie import compile_source
from solcx import compile_source, install_solc, compile_standard, set_solc_version
import json

# Install a compatible version of solc
set_solc_version('0.8.0')
# Read Solidity source code from file
with open('TournamentContract.sol', 'r') as file:
    source_code = file.read()

# Compile the contract
compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {
        "TournamentContract.sol": {
            "content": source_code
        }
    },
    "settings": {
        "outputSelection": {
            "*": {
                "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
            }
        }
    }
})

abi = compiled_sol['contracts']['TournamentContract.sol']['TournamentContract']['abi']
bytecode = compiled_sol['contracts']['TournamentContract.sol']['TournamentContract']['evm']['bytecode']['object']

with open('TournamentContractABI.json', 'w') as f:
    json.dump(abi, f)

with open('TournamentContractBytecode.txt', 'w') as f:
    f.write(bytecode)