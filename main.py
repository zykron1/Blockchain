import time
from networking import Node
from ecdsa import InvalidCurveError, SigningKey, NIST256p, VerifyingKey
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
                    node.peers.add((inp[3], inp[4]))
                if inp[2] == "remove":
                    node.peers.remove((inp[3], int(inp[4])))

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
                node.broadcast_transaction(transaction)

    except Exception as e:
        print("ERROR: ")
        print(e)
