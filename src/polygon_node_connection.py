import web3.eth
from web3 import Web3

# class nodeClient:
#     def __init__(self):
#         # metamask url
#         web3 = Web3(Web3.WebsocketProvider("wss://rpc-mumbai.maticvigil.com/ws"))
#
#         print(web3.isConnected())
#         # print(web3.eth.blockNumber)
#
#     """
#     def close_conenction(self):
#
#
#     """
#
#     def read_from_contract(self, ):
        
        
if __name__ == "__main__":
    import json
    from web3.contract import Contract
    from web3 import Web3, HTTPProvider
    w3 = Web3(provider=HTTPProvider(endpoint_uri="https://rpc-mumbai.maticvigil.com"))
    str_address = "0xD1A831348B69a37c75540ac3af58b6E37224fe64"
    address = Web3.toChecksumAddress(str_address)

    with open("funnel_abi.json", "r") as f:
        abi_file = json.load(f)

    contract: Contract = w3.eth.contract(address=address, abi=abi_file["abi"])
    for event in contract.events:
        print(event)

    for func in contract.functions:
        print(func)

    def fetch_events(
            event,
            argument_filters=None,
            from_block=None,
            to_block="latest",
            address=None,
            topics=None):

        from web3._utils.events import get_event_data
        from web3._utils.filters import construct_event_filter_params

        """Get events using eth_getLogs API.

        This is a stateless method, as opposite to createFilter and works with
        stateless nodes like QuikNode and Infura.

        :param event: Event instance from your contract.events
        :param argument_filters:
        :param from_block: Start block. Use 0 for all history/
        :param to_block: Fetch events until this contract
        :param address:
        :param topics:
        :return:
        """

        if from_block is None:
            raise TypeError("Missing mandatory keyword argument to getLogs: from_Block")

        abi = event._get_event_abi()
        abi_codec = event.web3.codec

        # Set up any indexed event filters if needed
        argument_filters = dict()
        _filters = dict(**argument_filters)

        data_filter_set, event_filter_params = construct_event_filter_params(
            abi,
            abi_codec,
            contract_address=event.address,
            argument_filters=_filters,
            fromBlock=from_block,
            toBlock=to_block,
            address=address,
            topics=topics,
        )

        # Call node over JSON-RPC API
        logs = event.web3.eth.getLogs(event_filter_params)

        # Convert raw binary event data to easily manipulable Python objects
        for entry in logs:
            data = get_event_data(abi_codec, abi, entry)
            yield data

    import time
    start_block = 24694644
    end_block   = 24697469

    while start_block < end_block:
        new_end_block = start_block + 1000
        for event in fetch_events(contract.events.PaymentMade, from_block=start_block, to_block=new_end_block):
            print(event)
        print(start_block, new_end_block)
        start_block = new_end_block
        time.sleep(3)

    # from web3 import Web3
    # from web3._utils.events import get_event_data
    # w3 = Web3(Web3.HTTPProvider("https://rpc-mumbai.maticvigil.com"))
    # contract = w3.eth.contract(address=address)
    # events = w3.eth.get_logs({'fromBlock': 24220510, 'toBlock': "latest", 'address': "0xd617d99f40b254f4614f5b9cc0090ca1383551a5"})
    #
    # def handle_event(event, event_template):
    #     try:
    #         result = get_event_data(event_template.web3.codec, event_template._get_event_abi(), event)
    #         return True, result
    #     except:
    #         return False, None
    #
    # for event in events:
    #     suc, res = handle_event(event=event, event_template=event_template)
    #     if suc:
    #         print("Event found", res)
