# Blockchain
Custom peer to peer blockchain network made from absolute scratch using raw tcp and a custom JSON RPC system.

## USAGE
Run main.py to launch the CLI

## Commands
### General
`node start <host> <port>`<br>
Launches a server at `<host>:<port>`

`node mempool`<br>
Prints out all current uncomfirmed unmined transactions currently in the mempool

### Blockchain
`node blockchain`<br>
Prints out the entire blockchain

`node blockchain save`<br>
Saves the serialized version of the blockchain into the `blockchain` file

`node blockchain load`<br>
Loads the blockchain from the serialized `blockchain` file

### Peer management
`node peers list`<br>
Lists out all the known peers

`node peers add <host> <port>`<br>
Adds a peer with the given info into memory

`node peers remove <host> <port>`<br>
Removes a peer with the given info from memory

`node peers save`<br>
Saves peer info into the KNOWN_NODES file(autoloads on startup of a node)

### Peer requests
`node request mempool`<br>
Requests the mempool from all known peers to sync up with the rest of the chain

`node request chain`<br>
Requests the entire blockchain past the last known block on your peer from all peers

`node request peers`<br>
Requests all the peers known by your known peers and adds them if not already in your list

### Block creation and management
`node block create`<br>
Creates a new block using all the uncomfirmed transactions in the mempool

`node block mine`<br>
Runs a sha256 based proof of work algorithm to get adequete work for the block

`node block broadcast`<br>
Broadcasts the newly created block to all known peers

### Wallets
`node wallet list`<br>
Lists all wallets currently saved in the wallets directory with their name, public address, and balance

`node wallet balance <wallet_address>`<br>
Prints out the balance of the given wallet

`node wallet select <wallet_name>`<br>
Selects the given wallet into memory

`node wallet send <wallet_address> <amount>`<br>
Sends the given amount to that address into the public mempool
