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
    aave.listenToEvents(latest, 5000)

if __name__ == '__main__':
    main()

