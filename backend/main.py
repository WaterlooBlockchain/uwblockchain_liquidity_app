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
    
    userAssetTuples = aave.listenToEvents(latest, 500)
    # print(userAssetTuples[0])
    # aave.fetchUserReserveData(userAssetTuples)
    # aave.userReserveTest(userAssetTuples)

    reserveContractService = ContractService(
        apiKey=os.getenv("API_KEY"), 
        nodeAddress=os.getenv("NODE_ADDRESS"),
        contractAddress="0x057835Ad21a177dbdd3090bB1CAE03EaCF78Fc6d"
    )
    contract = reserveContractService.connect()

    for user in userAssetTuples:
        print("-----------------------------")
        print("asset: " + user[1])
        print("user: " + user[0])
        result = contract.functions.getUserReserveData(user[1], user[0]).call()
        print(result)

if __name__ == '__main__':
    main()

