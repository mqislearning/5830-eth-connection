from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd


def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]



def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """


    if chain not in ['source', 'destination']:
        print(f"Invalid chain argument: {chain}. Must be 'source' or 'destination'.")
        return


    w3_current = connect_to(chain)
    other_chain = 'destination' if chain == 'source' else 'source'
    w3_other = connect_to(other_chain)

    contracts = {
        chain: {
            'web3': w3_current,
            'details': get_contract_info(chain, contract_info)
        },
        other_chain: {
            'web3': w3_other,
            'details': get_contract_info(other_chain, contract_info)
        }
    }


    contract_current = contracts[chain]['web3'].eth.contract(
        address=contracts[chain]['details']['address'],
        abi=contracts[chain]['details']['abi']
    )
    contract_other = contracts[other_chain]['web3'].eth.contract(
        address=contracts[other_chain]['details']['address'],
        abi=contracts[other_chain]['details']['abi']
    )

    pk = "0x7bf22e78491476695a0f472ea12d522be65584cedcdab14b85eecfa22b404d51"
    sending_account = w3_other.eth.account.from_key(pk)
    sender_addr = sending_account.address
    sender_nonce = w3_other.eth.get_transaction_count(sender_addr)


    event_map = {
        'source': {
            'event': 'Deposit',
            'target_func': 'wrap',
            'chain_id': 97
        },
        'destination': {
            'event': 'Unwrap',
            'target_func': 'withdraw',
            'chain_id': 43113
        }
    }

    chain_cfg = event_map[chain]


    latest_blk = w3_current.eth.block_number
    start_blk = max(0, latest_blk - 19)

    event_filter = getattr(contract_current.events, chain_cfg['event']).create_filter(
        from_block=start_blk,
        to_block=latest_blk
    )
    detected_events = event_filter.get_all_entries()

    for evt in detected_events:
        params = evt['args']

        if chain == 'source':
            token_addr = params['token']
            recipient_addr = params['recipient']
        else:
            token_addr = params['underlying_token']
            recipient_addr = params['to']

        amt = params['amount']

        tx = getattr(contract_other.functions, chain_cfg['target_func'])(
            token_addr, recipient_addr, amt
        ).build_transaction({
            'from': sender_addr,
            'nonce': sender_nonce,
            'gas': 300000,
            'gasPrice': w3_other.eth.gas_price,
            'chainId': chain_cfg['chain_id']
        })

        signed_tx = w3_other.eth.account.sign_transaction(tx, pk)
        tx_hash = w3_other.eth.send_raw_transaction(signed_tx.rawTransaction)
        w3_other.eth.wait_for_transaction_receipt(tx_hash)
        sender_nonce += 1

        