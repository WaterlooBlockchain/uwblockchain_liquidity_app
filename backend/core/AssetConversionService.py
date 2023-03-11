from typing import List, Tuple
from dotenv import load_dotenv
import os
from web3 import Web3
from utils.ContractService import ContractService

# AssetConverisonService
# Wrapper for asset conversion functionality.
class AssetConversionService(object):
    @classmethod
    def __init__(cls) -> None:
        assetContractMap = {}

    @classmethod
    def addNewAsset(cls, assetAddr):
        