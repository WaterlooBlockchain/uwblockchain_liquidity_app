from datetime import datetime
from distutils.log import warn
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

    @classmethod
    def collectUserData(cls):     
        userData = cls.getUserData()['users']
        
        data = []
        i = 0
        for user in userData:
            if (i % 50 == 0):
                print(f'Completed {i} fetches so far... current time is {datetime.now().strftime("%H:%M:%S")}')
                userWithdrawalDepositData = {'data': [user for user in data]}
        
                cls.updateWithdrawalDepositData(userWithdrawalDepositData)
                print("SUCCESS: new data written to pickle file.")
                data = []
            curUser = {}
            curUser['address'] = user
            curUser['withDrawalDepositData'] = cls.getUserPositions(user)
            data.append(curUser)
            i += 1
        
        userWithdrawalDepositData = {'data': [user for user in data]}
        
        cls.updateWithdrawalDepositData(userWithdrawalDepositData)
        print("SUCCESS: new data written to pickle file.")
    
    @classmethod   
    def listenToEvents(cls, fromBlock, toBlock) -> List[str]:
        eventDepositFilter = cls.contract.events.Deposit.createFilter(fromBlock=fromBlock, toBlock=toBlock)
        eventBorrowFilter = cls.contract.events.Borrow.createFilter(fromBlock=fromBlock, toBlock=toBlock)

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

    @classmethod
    def getLatestBlockNumber(cls):
        return cls.web3Instance.eth.get_block_number()

    @classmethod
    def getSymbolPriceMap(cls) -> dict:
        reserveList = cls.getReserveList()

        parent = pathlib.Path(__file__).parent.resolve()
        with open(parent / "../utils/priceOracle.abi", 'r') as input:
            priceOracleAbi = input.read()
                
        priceOracle = cls.web3Instance.eth.contract(address="0xA50ba011c48153De246E5192C8f9258A2ba79Ca9",
                                                    abi=priceOracleAbi)

        # Note. The prices in this map are in ETH. This is done by getting the price of 
        # the token from the Aave price oracle which is in WEI (see link below). We then
        # divide by 10**18 to get the price in ETH.
        symbolPriceMap = {}
        for reserve in reserveList:
            address = reserve['addr']
            symbol = reserve['symb']
            
            # see Wei: https://www.gemini.com/cryptopedia/satoshi-value-gwei-to-ether-to-wei-converter-eth-gwei#section-ethereum-denominations-ether-to-wei-gwei-to-ether-more
            priceInWei = priceOracle.functions.getAssetPrice(address).call()
            symbolPriceMap[symbol] = priceInWei / 10**18

        return symbolPriceMap

    @classmethod
    def getUsersWithTotalBalanceGreaterThan25Eth(cls):
        userData = cls.getWithdrawalDepositData()['data']

        symbolPriceMap = cls.getSymbolPriceMap()
        
        # From here, we iterate over the users positions. We can use the fact
        # that numTokens * symbolPriceMap['symb'] = price in eth.
        # Using this, we simply sum the price of a user's deposited assets
        # and only add them to our return value should they have more than 25ETH.
        usersWithOver25EthDeposited = []
        for user in userData:
            deposits = user['withDrawalDepositData']['deposits']
            usersEth = 0
            for token in deposits:
                if not token in symbolPriceMap:
                    print(f'Warning: Symbol {token} not found in price map.')
                    continue
                usersEth += deposits[token] * symbolPriceMap[token]
            
            if usersEth > 25:
                usersWithOver25EthDeposited.append(user)
        
        return usersWithOver25EthDeposited

    @classmethod
    def getTop25UsersByDeposits(cls):
        userData = cls.getWithdrawalDepositData()['data']

        symbolPriceMap = cls.getSymbolPriceMap()
        
        # find the 25 people with the most money
        userDepositPairs = []
        for user in userData:
            deposits = user['withDrawalDepositData']['deposits']
            usersEth = 0
            for token in deposits:
                if not token in symbolPriceMap:
                    print(f'Warning: Symbol {token} not found in price map.')
                    continue
                usersEth += deposits[token] * symbolPriceMap[token]
            
            userDepositPairs.append([usersEth, user['address']])
        
        sortedUsersAssetPairs = sorted(userDepositPairs, reverse=True)

        # For testing and curiousity purposes
        # print(sortedUsersAssetPairs[0:25])

        top25UserAddresses = [pair[1] for pair in sortedUsersAssetPairs[0:25]]

        # add them to a list
        top25Users = []
        for user in userData:
            if (user['address'] in top25UserAddresses):
                top25Users.append(user)

        return top25Users

    @classmethod
    def getTop25UsersAssetDistribution(cls):
        top25Users = cls.getTop25UsersByDeposits()
        symbolPriceMap = cls.getSymbolPriceMap()

        # note, this distribution is all in ETH.
        assetDistribution = {}
        for user in top25Users:
            deposits = user['withDrawalDepositData']['deposits']
            for token in deposits:
                if not token in symbolPriceMap:
                    print(f'Warning: Symbol {token} not found in price map.')
                    continue
                    
                tokenValInEth = deposits[token] * symbolPriceMap[token]
                if not token in assetDistribution:
                    assetDistribution[token] = tokenValInEth
                else:
                    assetDistribution[token] = assetDistribution[token] + tokenValInEth
        
        return assetDistribution
              
    # FOR DEMO PURPOSES ONLY
    # the object that you see returned below can be returned by calling getLongShortRatios.
    # As of 03/20/2023, this object contains long short ratios for users from the past 
    # week of activity on Aave that have deposits of greater than 25 ETH.
    @classmethod
    def getFilteredLongShortRatios(cls):
        return {'stETH': 'No withdrawals for this asset.', 'WETH': 1.015977975852611, 'USDC': 1.7855513747116156, 'SNX': 6.003800965763927, 'WBTC': 6.874576063474662, 'AAVE': 'No withdrawals for this asset.', 'LINK': 'No withdrawals for this asset.', 'BAT': 'No withdrawals for this asset.', 'DAI': 4.955617483899838, 'ENJ': 'No withdrawals for this asset.', 'CRV': 5.729205522815787, 'BAL': 0.2136250434155488, 'USDT': 1.0066858246015304, 'CVX': 0.000297976363620105, 'DPI': 4.438523944832224, 'xSUSHI': 'No withdrawals for this asset.', 'ENS': 'No withdrawals for this asset.', 'sUSD': 2.2055052313101924, 'LUSD': 2.4302662606769765, 'REN': 'No withdrawals for this asset.', 'FRAX': 0.6671290839363091, 'TUSD': 1.2788614330593502, 'AMPL': 0.22578876879889037, 'GUSD': 3.267078210380426, 'ZRX': 'No withdrawals for this asset.', 'USDP': 1.4339992956809806, 'UST': 0.0576543581538062, '1INCH': 0.30111912541170316}

    # FOR DEMO PURPOSES ONLY
    # similar to above. this can be achieved by calling getTop25UsersAssetDistribution()
    @classmethod
    def getTop25WalletDistribution(cls):
        return {'WBTC': 123225.60460380797, 'USDT': 101210.89566161446, 'USDC': 168387.73209150112, 'stETH': 396023.5590871998, 'UNI': 508.42047507889714, 'SNX': 75.20610773708988, 'ENS': 570.4605692505937, 'CRV': 79453.69975570311, 'WETH': 148734.61918025083, 'DAI': 124538.58572786815, 'MKR': 613.4385184319912, 'TUSD': 992.2628092231258, 'YFI': 57.51350928165873, 'DPI': 75.01545580177084, 'LINK': 976.6963306760402}

    @classmethod
    def getLongShortRatios(cls):
        userData = cls.getUsersWithTotalBalanceGreaterThan25Eth()

        positionMap = {}
        positionMap['deposits'] = {}
        positionMap['withdrawals'] = {}

        for user in userData:
            withdrawalDepositData = user['withDrawalDepositData']
            deposits = withdrawalDepositData['deposits']
            withdrawals = withdrawalDepositData['borrowed']

            for asset in deposits:
                if asset in positionMap['deposits']:
                    positionMap['deposits'][asset] = positionMap['deposits'][asset] + deposits[asset]
                else:
                    positionMap['deposits'][asset] = deposits[asset]
            
            for asset in withdrawals:
                if asset in positionMap['withdrawals']:
                    positionMap['withdrawals'][asset] = positionMap['withdrawals'][asset] + withdrawals[asset]
                else:
                    positionMap['withdrawals'][asset] = withdrawals[asset]
            
        longShortRatios = {}

        for asset in positionMap['deposits']:
            if (not asset in positionMap['withdrawals']):
                longShortRatios[asset] = 'No withdrawals for this asset.'
            else:
                longShortRatio = positionMap['deposits'][asset] / positionMap['withdrawals'][asset]

                # removing crazy noise for testing purposes
                if (abs(longShortRatio) < 10):
                    longShortRatios[asset] = positionMap['deposits'][asset] / positionMap['withdrawals'][asset]
        
        return longShortRatios

        
    @classmethod
    def updateUserList(cls):
        
        latest = cls.getLatestBlockNumber()
        userAssetTuples = cls.listenToEvents(latest, 100)
        
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

    @classmethod
    def fetchUsersFromLastMonth(cls):
        latest = cls.getLatestBlockNumber()
        # https://etherscan.io/chart/blocktime
        # estimating average blocktime over the past month-ish
        averageBlockTime = 12.5
        blocksInMonth = int((30 * 24 * 60 * 60) / averageBlockTime)
        blocksInWeek = int(blocksInMonth / 4)

        # here we're looping over events using a sliding window approach
        # with a window of size 500 blocks. we' continue sliding this
        # window back until we hit 'blocksInWeek'.
        userAssetTuples = []
        toBlock = cls.getLatestBlockNumber()
        fromBlock = toBlock - 500
        blocksTraversed = 0

        while blocksTraversed < blocksInMonth:
            newUserAssetTuples = cls.listenToEvents(fromBlock, toBlock)
            userAssetTuples += newUserAssetTuples
            toBlock = fromBlock - 1
            fromBlock -= 500
            blocksTraversed += 500
            print(f'fetchUsersFromLastMonth: complete 500 blocks, for a total of {blocksTraversed} blocks so far.')

        # printing length of userAssetTuples for testing purposes
        print(len(userAssetTuples))

        # we want to save only the users for use later. we map over
        # them, adding only the user addresses, to a new set
        users = {'users': set([tup[0] for tup in userAssetTuples])}

        # call updateUserData with the new user data, this function
        # actually handles writing the data to the pickle file.
        cls.updateUserData(users)

    @classmethod
    def getUserData(cls) -> List[object]:
        parent = pathlib.Path(__file__).parent.resolve()

        if not (parent / "userData.p").is_file():
            warn("getUserData: User data file is not present. You must call update user list first to populate.")
            return None

        with open(parent / "userData.p", 'rb') as input:
            userData = pickle.load(input)
        
        return userData

    @classmethod 
    def updateUserData(cls, newData: List[Tuple]) -> None:
        parent = pathlib.Path(__file__).parent.resolve()

        if not (parent / "userData.p").is_file():
            
            with open(parent / "userData.p", 'wb') as output:
                pickle.dump(newData, output)
                
        else:
            
            with open(parent / "userData.p", 'rb') as input:
                oldUserData = pickle.load(input)
                
            oldUserData['users'].union(newData['users'])

            with open(parent / "userData.p", 'wb') as output:
                pickle.dump(oldUserData, output)
        
        return None
    
    @classmethod
    def updateWithdrawalDepositData(cls, newData: object) -> None:
        parent = pathlib.Path(__file__).parent.resolve()

        if not (parent / "withdrawalDepositData.p").is_file():
            with open(parent / "withdrawalDepositData.p", 'wb') as output:
                pickle.dump(newData, output)
        else:
            oldWithdrawalDepositData = cls.getWithdrawalDepositData()

            oldWithdrawalDepositData['data'] += (newData['data'])

            with open(parent / "withdrawalDepositData.p", 'wb') as output:
                pickle.dump(oldWithdrawalDepositData, output)

    @classmethod
    def getWithdrawalDepositData(cls) -> List[object]:
        parent = pathlib.Path(__file__).parent.resolve()

        if not (parent / "withdrawalDepositData.p").is_file():
            warn("getWithdrawalDepositData: Withdrawal/Deposit file is not present. You must call collect user data first to populate.")
            return None

        with open(parent / "withdrawalDepositData.p", 'rb') as input:
            withdrawalDepositData = pickle.load(input)
        
        return withdrawalDepositData

    @classmethod
    def getReserveList(cls) -> List[object]:
        parent = pathlib.Path(__file__).parent.resolve()

        if not (parent / "reserveList.p").is_file():
            warn("getReserveList: Reserve list file is not present. You must call get user positions first to populate.")
            return None

        with open(parent / "reserveList.p", 'rb') as input:
            reserveListData = pickle.load(input)
        
        return reserveListData

    @classmethod
    def getUserPositions(cls, address):
        
        cls.updateUserList()
        
        parent = pathlib.Path(__file__).parent.resolve()
        
        if not (parent / "reserveList.p").is_file():
            
            reserveList = cls.contract.functions.getReservesList().call()
            
            reserveData = []
            
            with open(parent / "../utils/erc20.abi", 'r') as input:
                erc20_abi = input.read()
                
            with open(parent / "../utils/protocolDataProvider.abi", 'r') as input:
                dataProvider_abi = input.read()
                
            pdp_cntrct = cls.web3Instance.eth.contract(address="0x057835Ad21a177dbdd3090bB1CAE03EaCF78Fc6d",
                                                       abi=dataProvider_abi)
            
            for addr in reserveList:
                tkn_cntrct = cls.web3Instance.eth.contract(address=addr, abi=erc20_abi)
                
                reserveData.append({})
                reserveData[-1]['addr'] = addr
                reserveAddr = pdp_cntrct.functions.getReserveTokensAddresses(addr).call()
                if addr == "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2":
                    reserveData[-1]['symb'] = "MKR"
                    reserveData[-1]['aTknAddress'] = reserveAddr[0]
                    reserveData[-1]['varDebtAddress'] = reserveAddr[1]
                    reserveData[-1]['stabDebtAddress'] = reserveAddr[2]
                else:
                    reserveData[-1]['symb'] = tkn_cntrct.functions.symbol().call()
                    reserveData[-1]['aTknAddress'] = reserveAddr[0]
                    reserveData[-1]['varDebtAddress'] = reserveAddr[1]
                    reserveData[-1]['stabDebtAddress'] = reserveAddr[2]
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
                userData['deposits'][reserveData[i]['symb']] = cls.fetchUserReserveAmnt(address, reserveData[i]['symb'])
            if pair[1] == '1':
                userData['borrowed'][reserveData[i]['symb']] = cls.fetchUserReserveAmnt(address, reserveData[i]['symb'], True)

        return userData
    
    @classmethod
    def fetchUserReserveAmnt(cls, user, symb, debt=False):
        
        parent = pathlib.Path(__file__).parent.resolve()
        with open(parent / 'reserveList.p', 'rb') as input:
            reserveData = pickle.load(input)
        with open(parent / "../utils/erc20.abi", 'r') as input:
                erc20_abi = input.read()
            
        cnt = 0
        while cnt < len(reserveData):
            
            if reserveData[cnt]['symb'] == symb:
                
                break
            
            cnt += 1
            
        assert cnt != len(reserveData), "Could not find symbol"
            
        if not debt:
            
            aTknCntrct = cls.web3Instance.eth.contract(address=reserveData[cnt]['aTknAddress'],
                                                       abi=erc20_abi)
            
            return aTknCntrct.functions.balanceOf(user).call() / 10**aTknCntrct.functions.decimals().call()
        
        else:
            
            varDebtCntrct = cls.web3Instance.eth.contract(address=reserveData[cnt]['varDebtAddress'],
                                                          abi=erc20_abi)
            stabDebtCntrct = cls.web3Instance.eth.contract(address=reserveData[cnt]['stabDebtAddress'],
                                                           abi=erc20_abi)
            
            varBal = varDebtCntrct.functions.balanceOf(user).call() / 10**varDebtCntrct.functions.decimals().call()
            stabBal = stabDebtCntrct.functions.balanceOf(user).call() / 10**stabDebtCntrct.functions.decimals().call()
            
            return varBal + stabBal