from typing import List, Tuple
from dotenv import load_dotenv
import os
from web3 import Web3
import pathlib, pickle
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
        
    def listenToEvents(cls, latest, blockLength) -> List[str]:
        eventDepositFilter = cls.contract.events.Deposit.createFilter(fromBlock=latest-blockLength, toBlock='latest')
        eventBorrowFilter = cls.contract.events.Borrow.createFilter(fromBlock=latest-blockLength, toBlock='latest')

        userAssetTuples = []
        for event in eventDepositFilter.get_all_entries():
            userAddress = event['args']['user']
            blockNum = event['blockNumber']
            userAssetTuples.append((userAddress, blockNum))
            
        for event in eventBorrowFilter.get_all_entries():
            userAddress = event['args']['user']
            blockNum = event['blockNumber']
            userAssetTuples.append((userAddress, blockNum))
            
        return userAssetTuples

    def getLatestBlockNumber(cls):
        return cls.web3Instance.eth.get_block_number()

    # def fetchUserReserveData(cls, activeUsers: List[Tuple(str, str)]) -> List[Tuple(str, str)]:
    def fetchUserReserveData(cls, activeUsers):
        userReserveData = []
        for data in activeUsers:
            user = data[0]
            asset = data[1]
            
            print(cls.contract.functions.getUserAccountData(user).call())
            
    def updateUserList(cls):
        
        latest = cls.getLatestBlockNumber()
    
        userAssetTuples = cls.listenToEvents(latest, 5000)
        
        parent = pathlib.Path(__file__).parent.resolve()
        
        aaveUsers = {'users' : set([tup[0] for tup in userAssetTuples]),
                     'blockNum' : latest}
        
        if not (parent / "userData.p").is_file():
            
            with open(parent / "userData.p", 'wb') as output:
                pickle.dump(aaveUsers, output)
                
        else:
            
            with open(parent / "userData.p", 'rb') as input:
                oldUserData = pickle.load(input)
                
            oldUserData['users'].union(aaveUsers['users'])
            oldUserData['blockNum'] = aaveUsers['blockNum']
            
            with open(parent / "userData.p", 'wb') as output:
                pickle.dump(oldUserData, output)
                
    def getUserPositions(cls, address):
        
        cls.updateUserList()
        
        parent = pathlib.Path(__file__).parent.resolve()
        
        if not (parent / "reserveList.p").is_file():
            
            reserveList = cls.contract.functions.getReservesList().call()
            
            reserveData = []
            
            with open(parent / "../utils/erc20.abi", 'r') as input:
                erc20_abi = input.read()
            
            for addr in reserveList:
                tkn_cntrct = cls.web3Instance.eth.contract(address=addr, abi=erc20_abi)
                
                reserveData.append({})
                reserveData[-1]['addr'] = addr
                if addr == "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2":
                    reserveData[-1]['symb'] = "MKR"
                else:
                    reserveData[-1]['symb'] = tkn_cntrct.functions.symbol().call()
                reserveData[-1]['dec'] = tkn_cntrct.functions.decimals().call()
            
            with open(parent / "reserveList.p", 'wb') as output:
                pickle.dump(reserveData, output)
                
        else:
            
            with open(parent / 'reserveList.p', 'rb') as input:
                reserveData = pickle.load(input)
        
        userConfig = str(bin(cls.contract.functions.getUserConfiguration(address).call()[0])[2:])
        
        # Pad if necessary
        if len(userConfig) < 2*len(reserveData):
            userConfig = (2*len(reserveData)-len(userConfig))*"0" + userConfig
        
        # Break it into 2 character chunks, read from right to left
        #
        # https://docs.aave.com/developers/v/2.0/the-core-protocol/lendingpool#getuserconfiguration
        #
        # 00: Nothing
        # 10: Collateral, not borrowed
        # 01: Borrowed, not collateral
        # 11: Both collateral and borrowed
        
        userConfig = [userConfig[i:i+2] for i in range(0, len(userConfig), 2)]
        userConfig = userConfig[::-1]
        
        userData = {'deposits' : {}, 'borrowed' : {}}
        for i in range(len(userConfig)):
            pair = userConfig[i]
            if pair[0] == '1':
                userData['deposits'][reserveData[i]['symb']] = 0
            if pair[1] == '1':
                userData['borrowed'][reserveData[i]['symb']] = 0

        return userData