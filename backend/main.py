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
        print("-----------------------------")
        print("asset: " + user[1])
        print("user: " + user[0])
        result = contract.functions.getUserReserveData(user[1], user[0]).call()
        print("user reserve data...")
        print("currentATokenBalance: " + str(result[0]))
        print("currentStableDebt: " + str(result[1]))
        print("currentVariableDebt: " + str(result[2]))
        print("principalStableDebt: " + str(result[3]))
        print("scaledVariableDebt: " + str(result[4]))
        print("stableBorrowRate: "  + str(result[5]))
        print("liqudityRate: " + str(result[6]))
        print("stableRateLastUpdated: " + str(result[7]))
        print("usageAsCollateralEnabled: " + str(result[8]))
        print("-----------------------------")

if __name__ == '__main__':
    main()

