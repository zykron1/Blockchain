# Blockchain
Custom peer to peer blockchain network made from absolute scratch using raw tcp and a custom JSON RPC system.

## USAGE
Run main.py to launch the CLI

## Commands
`node start <host> <port>`
Launches a server at <host>:<port>

`node mempool`
Prints out all current uncomfirmed unmined transactions currently in the mempool

`node blockchain`
Prints out the entire blockchain

`node blockchain save`
Saves the serialized version of the blockchian into the `blockchain` file

`node blockchain load`
Loads the blockchain from the serialized `blockchain` file

`node peers list`
Lists out all the known peers

`node peers add <host> <port>`
Adds a peer with the given info into memory

`node peers remove <host> <port>`
Removes a peer with the given info from memory

`node block create`
Creates a new block using all the uncomfirmed transactions in the mempool

`node block mine`
Runs a sha256 based proof of work algorithm to get adequete work for the block

`node block broadcast`
Broadcasts the newly created block to all known peers

`node wallet list`
Lists all wallets currently saved in the wallets directory with their name, public address, and balance

`node wallet balance <wallet_address>`
Prints out the balance of the given wallet

`node wallet select <wallet_name>`
Selects the given wallet into memory

`node wallet send <wallet_address> <amount>`
Sends the given amount to that address into the public mempool
