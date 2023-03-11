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
    userAssetTuples = aave.listenToEvents(latest, 500)
    aave.calculateLongShortRatio(userAssetTuples[0][1])

    

if __name__ == '__main__':
    main()

