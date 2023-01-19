import hashlib
import math
from decimal import Decimal
from random import shuffle as random_shuffle
from enum import Enum
from dataclasses import dataclass
import string
import random 

DECIMAL_PRECISION: int = 8
EMPTY_NODE_HASH: bytes = b'\x00' * 32

class Side(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"

@dataclass
class Leaf:
    id: str
    balances: dict[str, str]


class Node():
    hash: bytes
    balances: dict[str, Decimal]

    '''
        Creates a Node represented by a hash (a sequence of bytes), and a dictionary of the balances.
        The dictionary consists of keys which represent currencies and decimals representing the corresponding amounts.
        The supplied Decimal values MUST be rounded up to 8 decimal values using ROUND_HALF_EVEN and must be positive.
    '''
    def __init__(self, hash: bytes, balance_dict: dict[str, Decimal]) -> None:
        self.hash = hash
        require(all(amount >= 0 for amount in balance_dict.values()), "All balances must be positive")
        self.balances = balance_dict

    def to_string(self) -> str:
        return f"{self.hash.hex()},{to_string(self.balances)}"

class ProofStep():
    side: Side
    hash: bytes
    balances: dict[str, Decimal]

    def __init__(self, side: Side, hash: bytes, balances: dict[str, Decimal]) -> None:
        self.side = side
        self.hash = hash 
        self.balances = balances

    def to_string(self) -> str:
        return f'{self.side},{self.hash.hex()},{to_string(self.balances)}'

class MerkleSumTree():
    tree: list[Node]
    leaves_map: dict[str, int]
    salt: str

    '''
        Builds a merkle sum tree given a list of tuples representing the tree leaves.
        Expects leaves to have length of a multiple of 2 and to be a list of tuples. If this is not true
        then empty nodes (with an EMPTY_NODE_HASH and an empty dictionary) will be used as leaves until
        a multiple of 2 is reached.

        The constructor expects the first parameter of each leaf to be the identificator of the leaf and the 
        second parameter to be a dictionary of balances where the key is the currency and the amount is the value.

        Each leaf stored in the tree is a tuple(hash(bytes('audit_id + id')), dict_balance) with the hash algorithm 
        supplied in the constructor or sha256 as default. The dict_balance complies with the following standard:

            - No balance is zero. The lack of balance for a currency implies the amount to be zero.
            - The balances are ordered alphabetically by curency.
            - The amounts are required to have 8 decimals with a HALF_EVEN rounding mode applied.

        The tree is internally stored as a flat list where node i is the parent of nodes 2i and 2i+1.
    '''
    def __init__(
        self, 
        leaves: list[Leaf], 
        hash_type: str = 'sha256', 
        salt: str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=100)),
        shuffle = True
    ) -> None:
        self.hash_function = getattr(hashlib, hash_type)
        total_leaves = get_next_pow_2(len(leaves))

        node_leaves = (
            # Each leaf is a tuple (audit_id:user_id, balance_dict)
            [Node(self.hash_function(str.encode(salt + leaf.id)).digest(), to_decimal_balance(leaf.balances)) for leaf in leaves] +
            [Node(EMPTY_NODE_HASH, dict()) for _ in range(total_leaves - len(leaves))]
        )

        if shuffle == True:
            random_shuffle(node_leaves)

        tree = (
            [None] * len(node_leaves) + node_leaves
        )

        self.leaves_map = dict()
        for i in range(len(node_leaves), len(tree)):
            hash = tree[i].hash
            if hash != b'\x00' * 32:
                self.leaves_map[hash] = i

        for i in range(len(node_leaves) - 1, 0, -1):
            tree[i] = self._combine_tree_nodes(tree[2*i], tree[2*i+1])

        self.tree = tree
        self.salt = salt

    '''
        Combines a left and right node to construct the parent node
        which is a tuple storing the concatenation of the hashes and balances
        and the sum of the balances.
    '''
    def _combine_tree_nodes(self, left: Node, right: Node) -> Node:
        return Node(
            self.hash_function(
                left.hash + str.encode(to_string(left.balances))
                +
                right.hash + str.encode(to_string(right.balances))
            ).digest(),
            combine_balances(left.balances, right.balances),
        )

    def get_root(self) -> Node:
        return self.tree[1]

    def get_nodes(self) -> list[Node]:
        return self.tree[1:]

    '''
        For a given leaf, gets the proof as a list of ProofSteps objects with the
        relevant information for each step to verify correctly. The id is the identificator
        of the leaf, the hash is computed and then the discovery starts.
    '''
    def get_proof(self, id: str) -> list[ProofStep]:
        proof_length = int(math.log(len(self.tree) - 1, 2))
        proof = []

        hash = self.hash_function(str.encode(self.salt + id)).digest()
        current_index = self.leaves_map[hash]

        for _ in range(proof_length):
            is_right = current_index % 2 != 0
            
            if is_right:
                sibling = self.tree[current_index - 1]
            else:
                sibling = self.tree[current_index + 1]

            proof.append(
                ProofStep(Side.RIGHT if not is_right else Side.LEFT, sibling.hash, sibling.balances)
            )
            current_index = current_index // 2
            
        return proof

'''
    Combines two dictionary of balances by summing the amounts of them where the key
    defines the currency name. If any key exists in one of the dictionaries and not on the other
    then the result is summing the existing balance with zero.
'''
def combine_balances(
    left_balances: dict[str, Decimal], 
    right_balances: dict[str, Decimal]
) -> dict[str, Decimal]:
    return { k: round(left_balances.get(k, Decimal(0)) + right_balances.get(k, Decimal(0)), DECIMAL_PRECISION) for k in set(left_balances) | set(right_balances) }

'''
    Stringify the balances that are given by a dictionary where each currency is a key and
    the amounts are the values. This standarizes the balance that must be used for hashing
    with the format of 'currency_1:amount_1,...,currency_N:amount_N' ordered alphabetically
    by currency.
'''
def to_string(balances: dict[str, Decimal]) -> str:
    return '|'.join(map(lambda x: f"{x[0]}:{x[1]}", sorted(balances.items())))

def to_decimal_balance(balance_dict: dict[str, str]) -> dict[str, Decimal]:
    return { k: round(Decimal(v), DECIMAL_PRECISION) for k, v in balance_dict.items() }

def verify_merkle_proof(root_node: Node, steps: list[ProofStep], salt: str, leaf: Leaf, hash_type: str = 'sha256'):
    hash_fun = getattr(hashlib, hash_type)
    node = Node(hash_fun(str.encode(salt + leaf.id)).digest(), to_decimal_balance(leaf.balances))
    verify_merkle_proof_from_leaf(root_node, steps, node, hash_type)

'''
    Verifies a merkle proof constisting of a list of proof steps for a leaf node. The verification process
    asserts at each step that the balance is greater or equal than zero for all balances and applies the 
    node combination process to construct the path to the root node. Finally it asserts that the root hash
    is the same as the obtained hash and that the root balances are the same as the obtained balances.
'''
def verify_merkle_proof_from_leaf(root_node: Node, steps: list[ProofStep], leaf_node: Node, hash_type: str = 'sha256') -> tuple[str, str]:
    hash_fun = getattr(hashlib, hash_type)
    current = leaf_node

    for idx, step in enumerate(steps):
        left = right = None 

        require(all(amount >= 0 for amount in step.balances.values()), "At least one balance was negative")
        require(all(amount >= 0 for amount in current.balances.values()), "At least one balance was negative")
        
        if step.side == Side.RIGHT:
            left = current.hash + str.encode(to_string(current.balances))
            right = step.hash + str.encode(to_string(step.balances))
            sum_balances = combine_balances(current.balances, step.balances)
        else:
            left = step.hash + str.encode(to_string(step.balances))
            right = current.hash + str.encode(to_string(current.balances))
            sum_balances = combine_balances(step.balances, current.balances)

        current = Node(hash_fun(left + right).digest(), sum_balances)
        print(f"Step {idx + 1}, hash: {current.hash.hex()}")

    require(current.hash == root_node.hash, "Root hash is not equal to obtained hash")
    require(current.balances == root_node.balances, "Root balances are not equal to obtained balances")

    return current.hash.hex(), to_string(current.balances)
    
def get_next_pow_2(n):
    p = 1
    while (p < n):
        p *= 2

    return p

def require(statement: bool, message: str):
     if not statement: raise Exception(message)
