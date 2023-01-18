# ContractService Service
# Author - Brayden Royston

# See for usage:
# https://docs.google.com/document/d/1gKsJmiblAfjasY_OGF_ZafNcyhGJEpKcBgNI8xg5AP0/edit?usp=sharing


from typing import Any
from web3 import Web3
from aiohttp import ClientSession
import requests

class ContractService(object):
    @classmethod
    def __init__(cls, apiKey, nodeAddress, contractAddress):
        cls.apiKey = apiKey
        cls.nodeAddress = nodeAddress
        cls.contractAddress = contractAddress

        if (cls.contractAddress == None or type(cls.contractAddress) != str):
            raise Exception("ContractService Error: expecting string for contract address.") 
        
        if (cls.apiKey == None or type(cls.apiKey) != str):
            raise Exception("ContractService Error: expecting string for API key.")
        
        if (cls.nodeAddress == None or type(cls.nodeAddress) != str):
            raise Exception("ContractService Error: expecting string for node address.")
        
    @classmethod
    def connect(cls):
        # create web3 instance
        try:
            cls.web3Instance = Web3(Web3.HTTPProvider(cls.nodeAddress))
        except:
            raise Exception("ContractService Error: web3 instantiation failed. Check nodeAddress.")
        
        # get ABI from contract address using ether scan
        try:
            esUrl = "https://api.etherscan.io/api"
            esModule = "contract"
            esAction = "getabi"

            url = f'{esUrl}?module={esModule}&action={esAction}&address={cls.contractAddress}&apiKey={cls.apiKey}'
            cls.abi = requests.get(url).json()['result']
        except:
            raise Exception("ContractService Error: Etherscan API ABI fetch failed. Check API key.")

        # use ABI to create a web3.py contract instance and return it
        try:
            newContract = cls.web3Instance.eth.contract(address=cls.contractAddress, abi=cls.abi)
            return newContract
        except:
            raise Exception("ContractService Error: web3 contract instantiation failed.")


        


        

        
    

