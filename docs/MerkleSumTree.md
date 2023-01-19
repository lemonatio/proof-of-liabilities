# Merkle Sum Tree

A Merkle Sum Tree (MST) is a data structure that has the same properties that a Merkle Tree has with an extra field
containing the balance of multiple assets. The leafs are labelled with the cryptopgraphic hash of the data block, in
this implementation a "merkle leaf hash" is created using a unique id and a salt value. The full merkle leaf
includes the balance of multiple assets.

The rest of the nodes of the tree are labelled by the hash of the labels of the child nodes, including the balances,
and the sum of all the balances. The root hash will contain a label with the hash of the labels of the nodes below
and the sum of the balances of all leafs.

## Creation of a MST

To create a MST we begin by creating a file containing unique ids and a list of balances associated with them, the
script must parse this file and adapt it to the interface defined in the `merkle.py` library. The creation of
the tree requires the data of the file which will be used to create the leafs. The rest of the tree is then created
with the algorithm described above and the following characteristics:

- If the balance of an asset is zero then it will not be stored. The non-existence of an asset implies the fact that the asset has zero balance.
- The amount of each asset must have 8 decimals.
- The tree will always be complete, in the case where there is not enough leafs to complete the last level, then it will be completed
  with leafs that will have a `0x00` hash and no balances.
- The nodes cannot have negative balances, when creating the tree we must assert that every node created has zero or positive balance.

To create a tree one must use the `MerkleSumTree` constructor in the following manner:

```
mst = MerkleSumTree(user_balances, hash_type, salt, shuffle)
```

Where each of the parameters are:

- `shuffle`: Allows choosing if leafs passed as parameters can be shuffled or not.
- `salt`: Defines the salt that will be used for the creation of the hash. By default an alphanumeric code is created.
- `hash_type`: Allows choosing between different hashing algorithms. The default algorithm is SHA256

## Storage

The storage of the tree is a plain list of nodes where node `i` is the parent of nodes `2i` and `2i+1` and the first node is in the
index number 1. The object also stores a map where each key is a leaf hash and every value is the position of the leaf in the tree.
This stores more data but gives fast access for proof generation where we only know the hash. The list also allows for rapid traversing
of the tree from bottom to top (and viceversa) since each parent (or child) is a factor of 2 away in the list of nodes.

## Algorithm

The algorithm to create the tree is iterative, it starts from the right-most leaf at the start and then iterates through each node
from right to left, from bottom to top, combining the child nodes to create a parent node.
The hashing computed consists of hashing the concatenation of the left child hash with the left child balance, plus the right child hash with the right child balance. That is:
```
H(p) = H(l_h + l_b + r_h + r_b)
```

## Generation of a Merkle Proof

The process of generating a Merkle Proof consists of, given a leaf hash, obtain a proof (that is, the list of necessary nodes to
reach the root hash) for the leaf. Since finding the path from a leaf to the root follows the algorithm described in the [algorithm](#algorithm)
section above, then we must only traverse the tree from bottom to top and return the siblings for each parent.

The proof is a list of `ProofStep` objects, each `ProofStep` has a side (which tells us if it is a left/right child), a hash (the node`s
hash) and a dictionary of balances (the balances for the references node).

The code for this generation can be found in the `get_proof` method of the `MerkleSumTree` class.
