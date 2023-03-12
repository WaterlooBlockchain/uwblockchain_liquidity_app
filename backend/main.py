from core.AaveLpService import AaveLpService
from utils.ContractService import ContractService
import os
from dotenv import load_dotenv

def main():
    # load your .env
    load_dotenv("./.env")

    # Aave
    aave = AaveLpService()
    latest = aave.getLatestBlockNumber()
    
    # smaller blocklength => smaller # of records
    userAssetTuples = aave.listenToEvents(latest, 5000)

    reserveContractService = ContractService(
        apiKey=os.getenv("API_KEY"), 
        nodeAddress=os.getenv("NODE_ADDRESS"),
        contractAddress="0x057835Ad21a177dbdd3090bB1CAE03EaCF78Fc6d"
    )
    contract = reserveContractService.connect()

    for user in userAssetTuples:
        print(f"user address: {user[0]}")
        print(f"blockNum: {user[1]}")
        print("-----------------------------")
        
    aave.updateUserList()
    aave.getUserPositions()

if __name__ == '__main__':
    main()

