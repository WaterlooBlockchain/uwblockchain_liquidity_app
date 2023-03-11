from core.AssetConversionService import AssetConversionService
from core.AaveLpService import AaveLpService
from utils.ContractService import ContractService
import os
from dotenv import load_dotenv

def main():
    # load your .env
    load_dotenv("./.env")

    # Aave
    aave = AaveLpService()
    assetConversionService = AssetConversionService()

    usdcAddr = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
    conversion = assetConversionService.getConversionScale(usdcAddr)
    
    latest = aave.getLatestBlockNumber()
    
    # smaller blocklength => smaller # of records
    userAssetTuples = aave.listenToEvents(latest, 500)

    reserveContractService = ContractService(
        apiKey=os.getenv("API_KEY"), 
        nodeAddress=os.getenv("NODE_ADDRESS"),
        contractAddress="0x057835Ad21a177dbdd3090bB1CAE03EaCF78Fc6d"
    )
    contract = reserveContractService.connect()

    for pair in userAssetTuples:
        user = pair[0]
        asset = pair[1]
        if (asset == '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'):
            result = contract.functions.getUserReserveData(asset, user).call()
            print(result)
            aToken = result[0]
            converted = aToken / (10 ** conversion)
            print("USDC Converted aToken Balance: " + str(converted))


if __name__ == '__main__':
    main()

