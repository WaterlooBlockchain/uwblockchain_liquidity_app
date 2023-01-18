from utils.ContractService import ContractService
import os
from dotenv import load_dotenv

def main():
    # load your .env
    load_dotenv("./.env")

    # use whatever contract address...
    contractAddress = "0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413"

    # use contract service to create a new web3 contract instance...
    contractService = ContractService(
        apiKey=os.getenv("API_KEY"), 
        nodeAddress=os.getenv("NODE_ADDRESS"), 
        contractAddress=contractAddress
    )
    myContract = contractService.connect()

    # do contract things...
    print(myContract.all_functions())

if __name__ == '__main__':
    main()

