from distutils.log import warn
import os
from utils.ContractService import ContractService

# AssetConverisonService
# Wrapper for asset conversion functionality.
class AssetConversionService(object):
    @classmethod
    def __init__(cls) -> None:
        cls.assetDecimalsMap = {
            '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': 6,
        }

    @classmethod
    def createOrUpdateAssetDecimal(cls, assetAddr, impAddr=None):
        try:
            contractService = ContractService(
                apiKey=os.getenv("API_KEY"), 
                nodeAddress=os.getenv("NODE_ADDRESS"),
                contractAddress=assetAddr,
                implementationAddress=impAddr
            )
            contract = contractService.connectImplementation()
        except:
            raise Exception("AssetConversionService: Failed to connect to contract.")
        
        try:
            cls.assetDecimalsMap[assetAddr] = contract.functions.decimals().call()
            print(cls.assetDecimalsMap[assetAddr])
        except:
            raise Exception("AssetConversionService: Failed to retrieve decimals from contract.")

    @classmethod
    def getConversionScale(cls, assetAddr):
        if (not assetAddr in cls.assetDecimalsMap):
            warn("AssetConversionService: Asset is not in conversion map. Add this asset with addNewAsset.")
            return -1
        return cls.assetDecimalsMap[assetAddr]

    @classmethod
    def updateUsdc(cls):
        usdcAddr = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        usdcImpAddr= "0xa2327a938febf5fec13bacfb16ae10ecbc4cbdcf"
        cls.createOrUpdateAssetDecimal(usdcAddr, usdcImpAddr)