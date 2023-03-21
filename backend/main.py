from core.AaveLpService import AaveLpService
from utils.ContractService import ContractService
import os, pickle
from dotenv import load_dotenv

def main():
    # Aave
    # Connect to AaveLpService
    aave = AaveLpService()

    # Fetch users from last month. These will be stored in 
    # userData.p
    # Note. This was last ran as of 03/19:8:55pm.
    # aave.fetchUsersFromLastMonth()

    # Output addresses in userData (testing purposes)
    # print(aave.getUserData())

    # Gather user data for addresses present in userData.
    # aave.collectUserData()
    # print(aave.getWithdrawalDepositData()['data'])
    # print(aave.getLongShortRatios())

    aave.getTop25UsersAssetDistribution()

if __name__ == '__main__':
    main()

