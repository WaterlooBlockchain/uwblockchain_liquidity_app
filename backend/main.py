from core.AaveLpService import AaveLpService
from utils.ContractService import ContractService
import os, pickle
from dotenv import load_dotenv

def main():
    # load your .env
    load_dotenv("./.env")

    # Aave
    aave = AaveLpService()

    reserveContractService = ContractService(
        apiKey=os.getenv("API_KEY"), 
        nodeAddress=os.getenv("NODE_ADDRESS"),
        contractAddress="0x057835Ad21a177dbdd3090bB1CAE03EaCF78Fc6d"
    )
    contract = reserveContractService.connect()
        
    aave.updateUserList()
    
    with open('core/userData.p', 'rb') as input:
        userData = pickle.load(input)
    
    for user in userData['users']:
        print(f'address: {user}')
        print(f'data: {aave.getUserPositions(user)}')

if __name__ == '__main__':
    main()

