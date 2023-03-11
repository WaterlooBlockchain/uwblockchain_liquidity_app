from dotenv import load_dotenv
import os
from web3 import Web3
from utils.ContractService import ContractService

# AaveLpService
# Encapsulates all functionality related to Aave
class AaveLpService(object):
    @classmethod
    def __init__(cls) -> None:
        # instantiate Contract Service
        load_dotenv("./.env")
        cls.contractAddress = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
        cls.contractImplementationAddress = "0xc6845a5c768bf8d7681249f8927877efda425baf"
        try:
            cls.contractService = ContractService(
                apiKey=os.getenv("API_KEY"), 
                nodeAddress=os.getenv("NODE_ADDRESS"),
                contractAddress=cls.contractAddress,
                implementationAddress=cls.contractImplementationAddress
            )
        except:
            raise Exception("Failed to create ContractService for AaveProtocolDataProvider contract. Verify your .env file.")

        # connect to the Aave contract
        try:
            cls.contract = cls.contractService.connectImplementation()
        except:
            raise Exception("Failed to connect to AaveProtocolDataProvider Contract.")
        
        try:
            cls.web3Instance = Web3(Web3.HTTPProvider(os.getenv("NODE_ADDRESS")))
        except:
            raise Exception("ContractService Error: web3 instantiation failed. Check nodeAddress.")
    
    @classmethod
    def listenToEvents(cls, latest, blockLength) -> List[str]:
        eventFilter = cls.contract.events.Withdraw.createFilter(fromBlock=latest-blockLength, toBlock='latest')

        userAssetTuples = []
        for event in eventFilter.get_all_entries():
            withdrawalAsset = event['args']['reserve']
            userAddress = event['args']['user']
            userAssetTuples.append((userAddress, withdrawalAsset))
        return userAssetTuples

    @classmethod
    def getLatestBlockNumber(cls):
        return cls.web3Instance.eth.get_block_number()

    @classmethod
    def fetchUserReserveData(cls, activeUsers):
        userReserveData = []
        for data in activeUsers:
            user = data[0]
            asset = data[1]
            
            print(cls.contract.functions.getUserAccountData(user).call())

    @classmethod
    def calculateLongShortRatio(cls, user):
        reserveList = cls.contract.functions.getReservesList().call()
        user = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'

        binaryUserConfig = cls.findUserConfig(user)

        assetBinaryPairMapping = cls.mapReservesToBinary(binaryUserConfig, reserveList)
        print(binaryUserConfig)

    @classmethod
    def findUserConfig(cls, user):
        # print(user)
        # hexConfig = "0x" + str(cls.contract.functions.getUserConfiguration(user).call()[0])
        # print(hexConfig)
        # decimalConfig = int(hexConfig)

        binaryConfig = "10101001001011101010101100000010011100010001000"
        return binaryConfig

    @classmethod
    def mapReservesToBinary(cls, binaryUserConfig, reserveList):
        print(len(binaryUserConfig))
        print(len(reserveList))

    @classmethod
    def getBalanceOf(cls, user):
        print(cls.contract.functions.balanceOf(user))
