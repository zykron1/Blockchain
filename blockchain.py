from typing import DefaultDict
from ecdsa import SigningKey, VerifyingKey, NIST256p, BadSignatureError
import hashlib
import json
import base64
import random


class Transaction:
    def __init__(self, nonce, sender, recipient, amount, signature):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature
        self.nonce = nonce

    @staticmethod
    def from_dict(data):
        return Transaction(
            data["transaction"]["nonce"],
            data["transaction"]["sender"],
            data["transaction"]["recipient"],
            data["transaction"]["amount"],
            data["signature"]
        )

    def to_internal_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "nonce": self.nonce
        }

    def to_external_dict(self):
        return {
            "signature": self.signature,
            "transaction": self.to_internal_dict()
        }

    def to_internal_json(self):
        return json.dumps(self.to_internal_dict())

    def generate_hash(self):
        return hashlib.sha256(self.to_internal_json().encode()).digest()

    def check_signature(self):
        if not self.signature or not self.sender:
            return False
        try:
            verifying_key = VerifyingKey.from_string(
                    base64.b64decode(self.sender),
                    curve=NIST256p
            )
            verifying_key.verify(
                    base64.b64decode(self.signature),
                    self.generate_hash()
            )
            return True
        except (BadSignatureError, ValueError):
            return False

    def sign_transaction(self, private_key: SigningKey):
        h = self.generate_hash()
        signature = private_key.sign(h)
        self.signature = base64.b64encode(signature).decode()

    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, Transaction):
            return self.to_external_dict() == value.to_external_dict()
        return False

    def __hash__(self):
        return hash(json.dumps(self.to_external_dict()))

    def __str__(self):
        return json.dumps(self.to_external_dict())

    def __repr__(self):
        return self.__str__()


class Block:
    def __init__(self, timestamp, prev_hash, nonce, transactions, work):
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.nonce = nonce
        self.transactions = transactions
        self.work = work

    @staticmethod
    def from_dict(data):
        return Block(
            data["timestamp"],
            data["prev_hash"],
            data["nonce"],
            [Transaction.from_dict(t) for t in data["transactions"]],
            data["work"]
        )

    def to_dict(self):
        return {
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "transactions": [transaction.to_external_dict() for transaction in self.transactions],
            "work": self.work
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def generate_hash(self):
        return hashlib.sha256(self.to_json().encode()).hexdigest()

    def check_work(self, n):
        h = self.generate_hash()
        return h.startswith('0' * n)

    def single_thread_mine(self, n):
        while True:
            self.work = random.randint(1, 1000000000000)
            if self.check_work(n):
                break

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return self.to_json()


class Blockchain:
    def __init__(self):
        self.chain = [
                Block(1752211185.0440528, None, 0, [
                    Transaction(
                        0,
                        None,
                        "JxOFiumQzTjid2lbCaXRIir6zWR6Zx9VDnx0GMeWr6VsNTHFv6fqzupE+c9jK4tUQeisXcoasDFEtr/PYY6qkA==",
                        5_000_000_000,
                        None
                        )
                ], None)
        ]
        self.balances = DefaultDict(int)
        self.nonces = DefaultDict(int)
        self.nonces[None] += 1
        self.mempool = set() 
        self.index_balances()

    def index_balances(self):
        for block in self.chain:
            for transaction in block.transactions:
                if not transaction.check_signature() and not block.nonce == 0:
                    continue
                self.balances[transaction.recipient] += transaction.amount
                self.balances[transaction.sender] -= transaction.amount

    def get_last_block(self):
        return self.chain[-1]

    def get_last_hash(self):
        return self.get_last_block().generate_hash()

    def validate_block(self, block):
        # 1) Validate block previous hash points to the correct previous block
        if not block.prev_hash == self.get_last_hash():
            print("Block validation failed: Previous hash does not point to correct previous block")
            return False

        # 2) Validate block has POW
        if not block.check_work(4):
            print("Block validation failed: Not enough proof of work")
            return False

        # 3) Validate every transaction in the block
        for transaction in block.transactions:
            if not self.validate_transaction(transaction, True):
                return False
        return True

    def validate_transaction(self, transaction, skip_mempool=False):
        # 1) Validate signature
        if not transaction.check_signature():
            print("Transaction validation failed: Transaction signature is invalid")
            return False

        # 2) Validate transaction balance
        sender = self.balances.get(transaction.sender)
        if not sender or not sender >= transaction.amount:
            print("Transaction validation failed: Insufficient balance")
            return False

        # 3) Validate transaction nonce
        if not self.nonces[transaction.sender] <= transaction.nonce:
            print("Transaction validation failed: Invalid nonce")
            return False

        # 4) Make sure transaction is not in the mempool
        if skip_mempool:
            return True
        for tx in self.mempool:
            if tx.sender == transaction.sender and tx.nonce == transaction.nonce:
                print(tx.sender, tx.nonce)
                print(transaction.sender, transaction.nonce)
                print(tx.to_external_dict())
                print(transaction.to_external_dict())
                print("Transaction validation failed: Duplicate nonce in mempool")
                return False

        return True

    def add_block(self, block):
        for transaction in block.transactions:
            # Remove transactions from mempool
            if transaction in self.mempool:
                self.mempool.remove(transaction)

            self.balances[transaction.recipient] += transaction.amount
            self.balances[transaction.sender] -= transaction.amount
            self.nonces[transaction.sender] = transaction.nonce 

        self.chain.append(block)

    def add_transaction(self, transaction):
        self.mempool.add(transaction)

    def __str__(self) -> str:
        return f"Blockchain(chain={self.chain}, mempool={self.mempool})"
    
    def __repr__(self):
        return self.__str__()
