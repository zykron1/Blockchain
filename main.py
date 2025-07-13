import json
import time
from networking import Node
from ecdsa import SigningKey, NIST256p
from blockchain import Block, Blockchain, Transaction
import os
import pickle
import base64

node = Node("", 0, Blockchain())
selected_wallet = None
signing_key = None
verifying_key = None
block = None
nonce = 0

while True:
    inp = input(">>> ")
    inp = inp.split(" ")
    try:
        if inp[0] == "node":
            if inp[1] == "start":
                node.host = inp[2]
                node.port = int(inp[3])
                node.peers.remove((inp[2], int(inp[3]))) # remove self as peer
                node.start()

            if inp[1] == "mempool":
                print(node.chain.mempool)

            if inp[1] == "blockchain":
                if len(inp) > 2:
                    if inp[2] == "save":
                        print("Saving blockchain to disk...")
                        pickle.dump(node.chain, open("blockchain", "wb"))
                        print("Saved to disk:")
                    if inp[2] == "load":
                        print("Loaded chain:")
                        node.chain = pickle.load(open("blockchain", "rb"))
                print(node.chain)

            if inp[1] == "peers":
                if inp[2] == "list":
                    print(node.peers)
                if inp[2] == "add":
                    node.peers.add((inp[3], int(inp[4])))
                if inp[2] == "remove":
                    node.peers.remove((inp[3], int(inp[4])))
                if inp[2] == "save":
                    with open("KNOWN_NODES", "w") as f:
                        w = ""
                        for peer in node.peers:
                            w += f"{peer[0]}:{peer[1]}\n"
                        f.write(w)

            if inp[1] == "request":
                if inp[2] == "mempool":
                    print(f"[NODE] Requesting mempool from {len(node.peers)} peer(s)")
                    for peer in node.peers:
                        try:
                            m = node.request_mempool(peer)
                            added = 0
                            for tx in m:
                                tx_obj = Transaction.from_dict(tx)
                                if tx_obj.check_signature():
                                    if tx_obj not in node.chain.mempool:
                                        node.chain.mempool.add(tx_obj)
                                        added += 1
                            print(f"[NODE] Received {len(m)} transaction(s) from {peer}, added {added} new")
                        except Exception as e:
                            print(f"[NODE] Failed to get mempool from {peer}: {e}")
                
                if inp[2] == "peers":
                    print(f"[NODE] Requesting peer list from {len(node.peers)} peer(s)")
                    for peer in list(node.peers):
                        try:
                            p = node.request_peers(peer)
                            added = 0
                            for new_peer in p:
                                new_peer = tuple(new_peer)
                                if new_peer != (node.host, node.port) and new_peer not in node.peers:
                                    node.peers.add(new_peer)
                                    added += 1
                            print(f"[NODE] Received {len(p)} peer(s) from {peer}, added {added} new")
                        except Exception as e:
                            print(f"[NODE] Failed to get peers from {peer}: {e}")
                
                if inp[2] == "height":
                    print(f"[NODE] Checking peer heights from {len(node.peers)} peer(s)")
                    max_height = len(node.chain.chain)
                    for peer in node.peers:
                        try:
                            h = node.request_height(peer)
                            print(f"[NODE] Peer {peer} has height {h}")
                            if h > max_height:
                                max_height = h
                        except Exception as e:
                            print(f"[NODE] Failed to get height from {peer}: {e}")
                    print(f"[NODE] Max height among peers: {max_height}")
                
                if inp[2] == "chain":
                    current_height = len(node.chain.chain)
                    peer_heights = {}
                    max_height = current_height
                
                    # Step 1: Gather peer heights
                    for peer in list(node.peers):
                        try:
                            h = node.request_height(peer)
                            peer_heights[peer] = h
                            if h > max_height:
                                max_height = h
                        except Exception as e:
                            print(f"[NODE] Failed to get height from {peer}: {e}")
                
                    # Step 2: Find peers with longer chains
                    candidate_peers = [peer for peer, height in peer_heights.items() if height > current_height]
                
                    if not candidate_peers:
                        print("[NODE] No peers have a longer chain.")
                    else:
                        print(f"[NODE] Trying to sync from {len(candidate_peers)} peer(s) with longer chains.")
                        for peer in candidate_peers:
                            print(f"[NODE] Attempting to sync missing blocks from peer {peer}")
                            temp_blockchain = Blockchain()
                            temp_blockchain.chain = node.chain.chain
                
                            try:
                                for i in range(current_height, peer_heights[peer]):
                                    block_data = node.request_block(peer, i)
                                    block = Block.from_dict(block_data)
                                    if not temp_blockchain.validate_block(block):
                                        raise Exception(f"[NODE] Invalid block received at height {i}")
                                    temp_blockchain.add_block(block)
                
                                # If successful, replace the main chain
                                node.chain = temp_blockchain
                                print(f"[NODE] Chain successfully extended to height {len(temp_blockchain.chain)} from peer {peer}")
                                break  # Stop after first valid extension
                
                            except Exception as e:
                                print(f"[NODE] Invalid chain from peer {peer}: {e}")
                                node.peers.discard(peer)  # Remove the peer permanently
                
                
            if inp[1] == "block":
                if inp[2] == "create":
                    print(f"Creating block with {len(node.chain.mempool)} transactions...")
                    last_block = node.chain.get_last_block()
                    block = Block(
                            time.time(),
                            node.chain.get_last_hash(),
                            last_block.nonce+1,
                            node.chain.mempool,
                            None
                    )
                    print("Block created!")
                if inp[2] == "mine":
                    if not block:
                        print("No block to mine!")
                        continue
                    print("Mining block...")
                    block.single_thread_mine(5)
                    print("Block mined!")
                if inp[2] == "broadcast":
                    node.broadcast_block(
                            block,
                    )

        if inp[0] == "wallet":
            if inp[1] == "list":
                wallets = os.listdir("wallets/")
                vk = []
                balances = []
                for wallet in wallets:
                    w = open("wallets/" + wallet, "r").read()
                    vk.append(w.split("\n")[1])
                    balances.append(node.chain.balances[w.split("\n")[1]])
                print("Name, Public Key, Balance")
                print("="*15)
                print("\n".join(f"{w}, {vk[i]}, {balances[i]}" for i, w in enumerate(wallets)))

            if inp[1] == "balance":
                print(node.chain.balances[inp[2]])

            if inp[1] == "select":
                selected_wallet = inp[2]
                print("Selected wallet: " + selected_wallet)
                file = open("wallets/" + selected_wallet, "r")
                signing_key = SigningKey.from_string(base64.b64decode(file.readlines()[0]), curve=NIST256p)
                verifying_key = signing_key.get_verifying_key()
                print("Loaded wallet")

            if inp[1] == "new":
                print(f"Creating wallet: '{inp[2]}'")
                sk = SigningKey.generate(curve=NIST256p)
                vk = sk.get_verifying_key()
                sk = base64.b64encode(sk.to_string()).decode()
                vk = base64.b64encode(vk.to_string()).decode()
                file = open("wallets/" + inp[2], "w")
                file.write(sk + "\n" + vk)
                file.close()

            if inp[1] == "send":
                recipient = inp[2]
                amount = int(inp[3])
                transaction = Transaction(
                        nonce,
                        base64.b64encode(verifying_key.to_string()).decode(),
                        recipient,
                        amount,
                        None
                )
                print(transaction.to_internal_json())
                concent = input("Sign transaction? (y/n) ")
                if concent == "y":
                    if not signing_key:
                        print("Key not selected!")
                        continue
                    transaction.sign_transaction(signing_key)
                    node.chain.add_transaction(transaction)
                    nonce += 1
                    print("Added transaction to mempool")
                    concent = input("Broadcast transaction? (y/n) ")
                    if concent == "y":
                        node.broadcast_transaction(transaction)
                else:
                    print("Transaction aborted")

    except Exception as e:
        print("ERROR: ")
        print(e)
