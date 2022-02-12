import json
from web3 import Web3

class nodeClient:
    def __init__(self):
        # metamask url
        web3 = Web3(Web3.WebsocketProvider("wss://rpc-mumbai.maticvigil.com/ws"))
    
        print(web3.isConnected())
        # print(web3.eth.blockNumber)

    """
    def close_conenction(self):


    """ 
    
    def read_from_contract(self, ):
        
        
if __name__ == "__main__":
    a = nodeClient()