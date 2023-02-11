from dotenv import load_dotenv
import os
from web3 import Web3
from utils.ContractService import ContractService

# AaveService
# Encapsulates all functionality related to Aave
# default instantiatiation will connect 
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
    
    def getLatestBlockNumber(cls):
        return cls.web3Instance.eth.get_block_number()
            
    def listenToEvents(cls, latest, blockLength) -> None:
        print("----------------- LISTENING TO EVENTS... -----------------")
        eventFilter = cls.contract.events.Withdraw.createFilter(fromBlock=latest-blockLength, toBlock='latest')
        # eventFilter = cls.web3Instance.eth.filter({
        #     'address': cls.contractAddress,
        #     'fromBlock': latest-blockLength,
        # })
        
        # while True:
        #     for event in eventFilter.get_new_entries():
        #         print("----------------- NEW EVENT -----------------")
        #         print(Web3.toJSON(event))
        print(len(eventFilter.get_all_entries()))
        for event in eventFilter.get_all_entries():
            print(event['args']['user'])
