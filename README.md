# Proof of Liabilities
This repository consists of three scripts and a library that can be viewed as different tools:

1.  The `merkle_leaf.py` script which given an id and an audit id generates the merkle leaf hash that is neccessary to verify a proof.
2.  The `verify.py` script which given a proof, a merkle leaf and the root node, verifies that the proof is correct.
3.  The `main.py` script which uses the library and an input file to create a Merkle Sum Tree and outputs the constructed tree and the proofs for each leaf of the tree.

The library can be found under the `lib` directory with the name `merkle.py` and it is a library to create and manage a Merkle Sum Tree.

We will now explain how to use each of these in a more detailed manner.

# Requisites

In order to use the scripts provided, the following requirements are needed:

- Python 3.9 or above

# Usage

## Obtaining the merkle leaf

To obtain a merkle leaf one must follow the script defined in `merkle_leaf.py` where, given an unique identifier and an audit id we obtain a merkle leaf hash. After that, we can add the balances to get a complete merkle leaf, although this is not needed until the verification or generation of a proof is necessary.

## Verifying a Merkle Proof

The process of verifying a Merkle Proof is quite straightforward: From the leaf, combine at each step the current node with the node referenced in each step of the proof with the algorithm described in the [algorithm](docs/MerkleTree.md#algorithm) section. Then at the last step we should obtain the root hash, we must assert that the hashes and the balances are equal to verify that the proof for that leaf is correct.

The script to verify a leaf can be found in the `verify.py` script in the repository. Here we start with a merkle leaf node (consisting of a hash and balances) and the root hash then we must assert that the root hash and balances are equal to the obtained result.

The script defined in `verify.py` can be called with the following arguments:

- `-i --input`: Defines the path to the file that will be used as input for the proof. When creating a Merkle Sum Tree the [outputs](#outputs) contain the proofs for all leafs.

- `-v --variables`: Defines a json file with variables that is needed to run the script, an example of the file is:

  ```json
  {
    "root_hash": "f9e645d2ffe5f17431c340df57e774189c06bd0b6cb0b646ae392d15fd6fcdd2",
    "root_balances": "ADA:33.55713700|ALGO:41.27807400|AVAX:0.10399078|AXS:0.02574917|BNB:0.01018535|BTC:19.10079686|DAI:13.22203900|ETH:0.01258170|LUNA:0.00064204|MATIC:69800.89997041|UNI:16.05900000|USDT:54599.82549300",
    "hash_algorithm": "sha256"
  }
  ```

All the displayed keys must be included in the file or the script will fail.
The execution of the script is as follows:

```bash
python3 verify.py -i input/proof.csv -v var.json
```

Where, following the example described above the file `proof.csv` should contain the output of the `main.py` and some additional information.

```
id,balances,proof,audit_id
00cf6625-9c3d-4e61-a17a-9820cae615cc,ADA:33.55713700|ALGO:41.27807400|AVAX:0.10399078|AXS:0.02574917|BNB:0.01018535|BTC:19.10069634|DAI:13.22203900|ETH:0.01258170|LUNA:0.00064204|MATIC:69800.89997041|UNI:16.05900000|USDT:54599.82549300,"[{RIGHT,c2eacf313cf93d1a77efaa27dee936ba526f65ce7cef0f510d8bb9f6ab59fd2e,BTC:0.00010052}]",2022-12-18-745ed8c9
```

After adding the correct information in the variables file and a correct proof, the verification should be done correctly.

## Creating a Merkle Sum Tree

The script defined in `main.py` can be called with the following arguments:

`-i --input`: Defines the path to the file that will be used as input

`-o --output`: Defines a list of paths, in order, where the output files will be generated. By default the first position defines the output of the tree, and the second one defines the output of the proofs for each leaf.

`-a --audit_id`: Defines an id for the audit that is being generated.

Each of these pair of (id, balances) will be represented by a leaf in the Merkle Sum Tree (MST), the identifier of each leaf is the merkle leaf hash created by hashing the unique identifier with the `audit_id`.

- For more information regarding the algorithm to create the tree, please see [this section](docs/MerkleSumTree.md#algorithm).

- For more information regarding the proof generation process, please see [Generation of a Merkle Proof](docs/MerkleSumTree.md#generation-of-a-merkle-proof).

### Outputs

After running the script an output will be generated in the paths provided in the parameter `output`. The first output file will have the tree, where each row is a node. The tree will be outputted in a csv file where the first column will output the hash of each node and the second one will be the balances. The order of the nodes is from top to bottom, from left to right.

The second output will have the proofs, where each row will have the first column as the unique identifier for each leaf and in the second column the merkle proof, containing of a list of steps to obtain the root hash from the leaf and assert it correctly.

### Example

An example input file is a CSV ordered with a unique identifier in the first column and a list of assets on the second column.

```
id, balances
00a2ee33-713b-44df-b9cf-c78aaa32ff3c, AAVE:0.00000000|ADA:0.00000000|ALGO:0.00000000|ATOM:0.00000000|AVAX:0.00000000|AXS:0.00000000|BNB:0.00000000|BTC:0.00010052|BUSD:0.00000000|CAKE:0.00000000|DAI:0.00000000|DOGE:0.00000000|DOT:0.00000000|ENS:0.00000000|ETH:0.00000000|FTM:0.00000000|LUNA:0.00000000|LUNA2:0.00000000|MANA:0.00000000|MATIC:0.00000000|NEAR:0.00000000|PAXG:0.00000000|SAND:0.00000000|SHIB:0.00000000|SLP:0.00000000|SOL:0.00000000|TRX:0.00000000|UNI:0.00000000|USDC:0.00000000|USDT:0.00000000|UST:0.00000000
00cf6625-9c3d-4e61-a17a-9820cae615cc, AAVE:0.00000000|ADA:33.55713700|ALGO:41.27807400|ATOM:0.00000000|AVAX:0.10399078|AXS:0.02574917|BNB:0.01018535|BTC:19.10069634|BUSD:0.00000000|CAKE:0.00000000|DAI:13.22203900|DOGE:0.00000000|DOT:0.00000000|ENS:0.00000000|ETH:0.01258170|FTM:0.00000000|LUNA:0.00064204|LUNA2:0.00000000|MANA:0.00000000|MATIC:69800.89997041|NEAR:0.00000000|PAXG:0.00000000|SAND:0.00000000|SHIB:0.00000000|SLP:0.00000000|SOL:0.00000000|TRX:0.00000000|UNI:16.05900000|USDC:0.00000000|USDT:54599.82549300|UST:0.00000000
```

To run the script we call the script with the desired parameters, for example

```bash
python3 main.py -i input/users.csv -o output/tree.csv output/proofs.csv -a 2022-12-18-745ed8c9
```

First output example:

```
f9e645d2ffe5f17431c340df57e774189c06bd0b6cb0b646ae392d15fd6fcdd2,ADA:33.55713700|ALGO:41.27807400|AVAX:0.10399078|AXS:0.02574917|BNB:0.01018535|BTC:19.10079686|DAI:13.22203900|ETH:0.01258170|LUNA:0.00064204|MATIC:69800.89997041|UNI:16.05900000|USDT:54599.82549300
bcb31f5742cd9a600115a84c8cb9f9422e877ab138239be5160a5c1c6488e5c4,ADA:33.55713700|ALGO:41.27807400|AVAX:0.10399078|AXS:0.02574917|BNB:0.01018535|BTC:19.10069634|DAI:13.22203900|ETH:0.01258170|LUNA:0.00064204|MATIC:69800.89997041|UNI:16.05900000|USDT:54599.82549300
c2eacf313cf93d1a77efaa27dee936ba526f65ce7cef0f510d8bb9f6ab59fd2e,BTC:0.00010052
```

Second output example:

```
00a2ee33-713b-44df-b9cf-c78aaa32ff3c,"[{LEFT,bcb31f5742cd9a600115a84c8cb9f9422e877ab138239be5160a5c1c6488e5c4,ADA:33.55713700|ALGO:41.27807400|AVAX:0.10399078|AXS:0.02574917|BNB:0.01018535|BTC:19.10069634|DAI:13.22203900|ETH:0.01258170|LUNA:0.00064204|MATIC:69800.89997041|UNI:16.05900000|USDT:54599.82549300}]"
00cf6625-9c3d-4e61-a17a-9820cae615cc,"[{RIGHT,c2eacf313cf93d1a77efaa27dee936ba526f65ce7cef0f510d8bb9f6ab59fd2e,BTC:0.00010052}]"
```

# Tests
## Unit Tests
Unit tests were created for the `merkle.py` library where the core functionalities of the project rely.
To run them you can use:
```bash
python -m unittest discover -s test
```
