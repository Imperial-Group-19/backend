import asyncio
import json
import operator
from logging import Logger
from typing import List
from hexbytes import HexBytes

from eth_typing.evm import ChecksumAddress
from web3 import Web3, HTTPProvider
from web3._utils.filters import construct_event_filter_params
from web3._utils.rpc_abi import RPC
from web3.contract import ContractEvent, Contract
from eth_abi import decode_abi
from db_objects import FunnelContractEvent
from https_connection import HTTPSConnection


class PolygonNodeClient:
    def __init__(self, event_loop: asyncio.AbstractEventLoop, logger: Logger, https_url: str,
                 contract_address: str, contract_abi_file: str, start_block: int):
        self.__event_loop = event_loop
        self.__https_url: str = https_url
        self.__start_block: int = start_block

        self.__web3: Web3 = Web3(provider=HTTPProvider(endpoint_uri=https_url))
        self.__contract_address: ChecksumAddress = Web3.toChecksumAddress(contract_address)
        self.__abi: dict = {}
        self.__logging = logger

        with open(contract_abi_file, "r") as f:
            self.__abi = json.load(f)

        if not self.__abi:
            raise Exception(f"ABI dict is empty. Check if file is correct: {contract_abi_file}")

        self.__contract: Contract = self.__web3.eth.contract(address=self.__contract_address, abi=self.__abi["abi"])
        self.__https_connection = HTTPSConnection(base_url=https_url, logger=self.__logging)
        self.__json_rpc_counter = 0
        self.__max_block_increase = 1000
        self.__event_callbacks = {}

        self.__event_loop.create_task(self.fetch_all_events())

    def get_events(self):
        return self.__contract.events

    async def fetch_all_events(self):
        latest_block = await self.fetch_latest_block()
        if latest_block is None:
            raise Exception(f"Failed to fetch latest block!")

        end_block = self.__start_block + 1000
        self.__logging.warning(f"Entering catch up phase: {self.__start_block} -->> {latest_block}")
        while end_block < latest_block:
            all_event_outputs = []
            for event in self.get_events():
                valid_output, event_outputs = await self.fetch_event(event=event, from_block=self.__start_block, to_block=end_block)
                if valid_output:
                    all_event_outputs.extend(event_outputs)

                await asyncio.sleep(5)

            all_event_outputs.sort(key=lambda x: (x.block_number, x.transaction_idx))

            for cb in self.__event_callbacks.values():
                cb(all_event_outputs)

            self.__start_block = end_block
            end_block = self.__start_block + self.__max_block_increase

        self.__logging.warning(f"Entering in line phase: {self.__start_block} -->> {latest_block}")
        while True:
            latest_block = await self.fetch_latest_block()
            if latest_block is None:
                raise Exception(f"Failed to fetch latest block!")

            all_event_outputs = []
            for event in self.get_events():
                valid_output, event_outputs = await self.fetch_event(event=event, from_block=self.__start_block, to_block=latest_block)
                if valid_output:
                    all_event_outputs.extend(event_outputs)

                await asyncio.sleep(5)

            all_event_outputs.sort(key=lambda x: (x.block_number, x.transaction_idx))

            for cb in self.__event_callbacks.values():
                cb(all_event_outputs)

            self.__start_block = latest_block
            await asyncio.sleep(5)

    def register_event_callback(self, idx: str, cb):
        self.__event_callbacks[idx] = cb

    async def fetch_latest_block(self):
        counter = 0
        while counter < 5:
            body = {
                "jsonrpc": "2.0",
                "method" : RPC.eth_blockNumber,
                "id"     : self.__json_rpc_counter
            }
            self.__json_rpc_counter += 1
            try:
                response = await self.__https_connection.fetch(path="", method="post", body=json.dumps(body))
                if "result" in response:
                    return int(response["result"], 16)
                else:
                    raise Exception(f"Received error message: {response}")
            except Exception as e:
                self.__logging.warning(f"Failed to fetch latest block: {e}")
                counter += 1
                await asyncio.sleep(5)

        return None

    async def fetch_event(self, event: ContractEvent, from_block=None, to_block="latest") -> (bool, List[FunnelContractEvent]):
        if from_block is None:
            raise TypeError("Missing mandatory keyword argument to getLogs: from_Block")
        abi = event._get_event_abi()
        abi_codec = event.web3.codec
        data_filter_set, event_filter_params = construct_event_filter_params(
            abi,
            abi_codec,
            contract_address=event.address,
            argument_filters={},
            fromBlock=from_block,
            toBlock=to_block,
            address=None,
            topics=None,
        )

        event_filter_params["fromBlock"] = hex(event_filter_params["fromBlock"])
        event_filter_params["toBlock"]  = hex(event_filter_params["toBlock"]) if isinstance(to_block, int) else to_block
        body = {
            "jsonrpc": "2.0",
            "method" : RPC.eth_getLogs,
            "params" : [event_filter_params],
            "id"     : self.__json_rpc_counter
        }

        self.__json_rpc_counter += 1

        try:
            response = await self.__https_connection.fetch(path="", method="post", body=json.dumps(body))
            if "result" in response:
                result = response["result"]
            else:
                raise Exception(f"Received error message: {response}")
        except Exception as e:
            self.__logging.warning(f"Raised exception whilst fetching event: {event}, {from_block}, {to_block}, {e}")
            return False, []

        output_result = []
        if result:
            decode_param_names = []
            decode_param_types = []
            for input in abi["inputs"]:
                decode_param_names.append(input["name"])
                decode_param_types.append(input["type"])

            for res in result:
                decoded_info = decode_abi(decode_param_types, HexBytes(res["data"]))
                event_data = {}
                for idx, param_name in enumerate(decode_param_names):
                    event_data[param_name] = decoded_info[idx]
                output_result.append(
                    FunnelContractEvent(
                        block_hash=res["blockHash"],
                        transaction_hash=res["transactionHash"],
                        address=res["address"],
                        block_number=int(res["blockNumber"], 16),
                        data=res["data"],
                        transaction_idx=int(res["transactionIndex"], 16),
                        event=abi["name"],
                        event_data=event_data
                    )
                )

        return True, output_result

        
if __name__ == "__main__":
    import logging
    import asyncio

    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()

    polygon = PolygonNodeClient(
        event_loop=loop,
        logger=logging, https_url="https://rpc-mumbai.maticvigil.com",
        contract_address="0xF9cc7D93484Cf2C64e2892d332F820495D2BDC2e",
        contract_abi_file="funnel_abi.json",
        start_block=24934959
    )

    for event in polygon.get_events():
        print(event)

    def dummy_callback(event):
        print(event)

    polygon.register_event_callback("dummy", dummy_callback)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
