import socket
import json
import blockchain
import threading


class Node:
    def __init__(self, host: str, port: int, chain: blockchain.Blockchain):
        self.host = host
        self.port = port
        self.chain = chain
        self.peers = set()
        self.load_peers()

    def load_peers(self):
        with open("KNOWN_NODES", "r") as f:
            for line in f.readlines():
                h = line.split(":")[0]
                p = int(line.split(":")[1])
                self.peers.add((h, p))

    # !!SERVER CODE!!
    def start(self):
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def listen_for_peers(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"[NODE] Listening on {self.host}:{self.port}")
        while True:
            conn, address = server.accept()
            threading.Thread(
                    target=self.handle_peer,
                    args=(conn, address),
                    daemon=True
            ).start()

    def handle_peer(self, conn, address):
        print(f"[NODE] Accepted connection from {address}")
        try:
            data = conn.recv(4096).decode()
            message = json.loads(data)
            self.handle_message(message, conn)
        except Exception as e:
            print("[NODE] ERROR: ", e)
        finally:
            conn.close()

    def handle_message(self, message, conn):
        message_type = message.get("type")
        message_data = message.get("data")
        message_from = message.get("from")
        message_parameter = message.get("parameter")
        if not message_type:
            return
        if message_type.startswith("new_") and not message_from:
            return
        if not message_data and not message_type.startswith("get_"):
            return
        if not message_parameter and message_type == "get_block":
            return
        if message_type == "new_block":
            self.new_block(conn, message_data, message_from)
        if message_type == "new_transaction":
            self.new_transaction(conn, message_data, message_from)
        if message_type == "get_block":
            self.get_block(conn, message_parameter)
        if message_type == "get_height":
            self.get_height(conn)
        if message_type == "get_mempool":
            self.get_mempool(conn)
        if message_type == "get_peers":
            self.get_peers(conn)
        if message_type == "get_ping":
            self.get_ping(conn)

    def new_block(self, conn, data, f):
        try:
            block = blockchain.Block.from_dict(json.loads(data))
        except Exception as e:
            print("[NODE] Failed to parse block: ", e)
            conn.send(json.dumps({
                "type": "error", "data": "Failed to parse block"
            }).encode())
            return
        if not self.chain.validate_block(block):
            print("[NODE] Invalid block recieved!")
            conn.send(json.dumps({
                "type": "error", "data": "Invalid block"
            }).encode())
            return
        self.chain.add_block(block)
        print("[NODE] Added block to chain!")
        self.broadcast_block(block, [f,])  # Spread the word about the new block

    def new_transaction(self, conn, data, f):
        try:
            transaction = blockchain.Transaction.from_dict(data)
        except Exception as e:
            print("[NODE] Failed to parse transaction: ", e)
            conn.send(json.dumps({
                "type": "error", "data": "Failed to parse transaction"
            }).encode())
            return
        if not self.chain.validate_transaction(transaction):
            print("[NODE] Transaction signature invalid!")
            conn.send(json.dumps({
                "type": "error", "data": "Invalid signature"
            }).encode())
            return
        if not transaction in self.chain.mempool:
            self.broadcast_transaction(transaction, ignore=[f,])
        self.chain.add_transaction(transaction)

    def get_block(self, conn, message_parameter):
        conn.send(json.dumps({
            "block": self.chain.chain[int(message_parameter)].to_dict()
        }).encode())

    def get_height(self, conn):
        conn.send(json.dumps({
            "height": len(self.chain.chain)
        }).encode())

    def get_mempool(self, conn):
        print(f"Sending mempool: {self.chain.mempool}")
        conn.send(json.dumps({
            "pool": [transaction.to_external_dict() for transaction in list(self.chain.mempool)]
        }).encode())

    def get_peers(self, conn):
        conn.send(json.dumps({
            "peers": list(self.peers)
        }).encode())

    def get_ping(self, conn):
        conn.send(json.dumps({
            "ping": True
        }).encode())

    # !!CLIENT CODE!!
    def broadcast_block(self, block, ignore=[]):
        print(f"[NODE] Broadcasting Block to {len(self.peers)} peers")
        origin = (self.host, self.port)
        for index, peer in enumerate(list(self.peers)):
            if peer in ignore:
                continue
            try:
                print(f"[NODE] Sending block to peer {index + 1}/{len(self.peers)}")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(peer)
                s.send(json.dumps({
                    "type": "new_block", "from": origin, "data": block.to_json()
                }).encode())
                s.close()
            except Exception as e:
                print(f"[NODE] Failed to block send to {peer} with error {e}")

    def broadcast_transaction(self, transaction, ignore=[]):
        print(f"[NODE] Broadcasting Transaction to {len(self.peers)} peers")
        origin = (self.host, self.port)
        print(f"origin: {origin}")
        for index, peer in enumerate(list(self.peers)):
            if list(peer) in ignore:
                continue
            try:
                print(f"[NODE] Sending transaction to peer {index + 1}/{len(self.peers)}")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(peer)
                s.send(json.dumps({
                    "type": "new_transaction", "from": origin, "data": transaction.to_external_dict()
                }).encode())
                s.close()
            except Exception as e:
                print(f"[NODE] Failed to send transaction to {peer} with error {e}")

    def request_height(self, peer):
        # Connect to peer and reqeuest height
        print(f"[NODE] Requesting height from {peer}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(peer)
        s.send(json.dumps({
            "type": "get_height"
        }).encode())
        height = json.loads(s.recv(4096).decode())["height"]
        s.close()
        return height

    def request_mempool(self, peer):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(peer)
        s.send(json.dumps({
            "type": "get_mempool"
        }).encode())
        pool = json.loads(s.recv(4096).decode())["pool"]
        s.close()
        return pool

    def request_peers(self, peer):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(peer)
        s.send(json.dumps({
            "type": "get_peers"
        }).encode())
        peers = json.loads(s.recv(4096).decode())["peers"]
        s.close()
        return peers

    def request_block(self, peer, block_ind):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(peer)
        s.send(json.dumps({
            "type": "get_block", "parameter": block_ind
        }).encode())
        block = json.loads(s.recv(4096).decode())["block"]
        s.close()
        return block
