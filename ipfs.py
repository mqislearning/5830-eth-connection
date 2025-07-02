import requests
import json

PIN_JSON_TO_IPFS_URL = 'https://api.pinata.cloud/pinning/pinJSONToIPFS'
GET_FROM_IPFS_URL = 'https://gateway.pinata.cloud/ipfs/'

def pin_to_ipfs(data):
    assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
    headers = {
        'pinata_api_key': "421c8fe5c272efa24398",
        'pinata_secret_api_key': "c26b2e88a04874929c79431ec51c1e2cc640e2e89ec99faca2244e07068c6d52"
    }
    
    files = {
        'file': ('data.json', json_data)
    }
    response = requests.post(PIN_JSON_TO_IPFS_URL, json=data, headers=headers)
    
    if response.status_code == 200:
	cid = response.json()["IpfsHash"]
	return cid
    else:
	raise Exception(f"Pinning failed: {response.text}")

def get_from_ipfs(cid,content_type="json"):
    assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE	
    response = requests.get(f"{GET_FROM_IPFS_URL}{cid}")
    
    if response.status_code == 200:
	if content_type == "json":
	    data = response.json()
	    assert isinstance(data, dict), "get_from_ipfs should return a dict"
	    return data
	else:
	    raise Exception("Only JSON content is supported")
    else:
	raise Exception(f"Fetching from IPFS failed: {response.text}")



