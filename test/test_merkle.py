import unittest
from lib.merkle import MerkleSumTree, Leaf, Node, to_string, combine_balances, to_decimal_balance, Side, verify_merkle_proof, ProofStep
import hashlib
from decimal import Decimal

INIT_LEAVES = [
    Leaf('fe775012-22ba-11eb-9221-0242ac1201ac', dict({'BTC': '0.00000001', 'ETH': '0.12312030'})),
    Leaf('fe775012-22ba-11eb-9221-0242ac1201ad', dict({'BTC': '0.00000002', 'ETH': '0.00000000'})),
    Leaf('fe775012-22ba-11eb-9221-0242ac1201ae', dict({'BTC': '1.12000001', 'ETH': '0.10123123'})),
    Leaf('fe775012-22ba-11eb-9221-0242ac1201af', dict({'BTC': '0.00100010', 'ETH': '5.12339900'}))
]
INIT_AUDIT_ID = '2022-12-31-fe775123'
    
class MerkleSumTreeTest(unittest.TestCase):
    def setUp(self) -> None:
        leaves = INIT_LEAVES
        audit_id = INIT_AUDIT_ID

        self.tree = MerkleSumTree(leaves = leaves, salt = audit_id, shuffle = False)

    def test_tree_correct_size(self):
        self.assertEqual(len(self.tree.get_nodes()), 7)

    def test_tree_node_integrity(self):
        nodes = self.tree.get_nodes()

        # Check leaf hashes
        leaf_offset = 3
        for idx, leaf in enumerate(INIT_LEAVES):
            expected_leaf_hash = hashlib.sha256(str.encode(f"{INIT_AUDIT_ID}{leaf.id}")).digest()
            expected_leaf_balances = leaf.balances

            actual_hash = nodes[leaf_offset + idx].hash
            actual_balances = nodes[leaf_offset + idx].balances

            self.assertEqual(actual_hash, expected_leaf_hash)
            self.assertEqual(actual_balances, to_decimal_balance(expected_leaf_balances))

        # Check intermediate node hashes
        for i in range(leaf_offset, len(nodes), 2):
            left_node, right_node = nodes[i], nodes[i+1]
            
            expected_parent_node_hash = hashlib.sha256(
                left_node.hash + str.encode(to_string(left_node.balances)) + right_node.hash + str.encode(to_string(right_node.balances))
            ).digest()
            expected_parent_node_balances = combine_balances(left_node.balances, right_node.balances)

            actual_hash = nodes[i // 2].hash
            actual_balances = nodes[i // 2].balances

            self.assertEqual(actual_hash, expected_parent_node_hash)
            self.assertEqual(actual_balances, expected_parent_node_balances)


        # Check root hash
        root = self.tree.get_root()
        
        expected_root_hash = hashlib.sha256(
            nodes[1].hash + str.encode(to_string(nodes[1].balances)) + nodes[2].hash + str.encode(to_string(nodes[2].balances))
        ).digest()
        expected_root_balances = combine_balances(nodes[1].balances, nodes[2].balances)

        self.assertEqual(root.hash, expected_root_hash)
        self.assertEqual(root.balances, expected_root_balances)

    def test_get_proof_correctly(self):
        # Given
        leaf = INIT_LEAVES[0]

        # When
        proof = self.tree.get_proof(leaf.id)

        # Then
        self.assertEqual(len(proof), 2)

        self.assertEqual(proof[0].side, Side.RIGHT)
        self.assertEqual(proof[0].hash.hex(), hashlib.sha256(str.encode(f"{INIT_AUDIT_ID}{INIT_LEAVES[1].id}")).digest().hex())
        self.assertEqual(proof[0].balances, to_decimal_balance(INIT_LEAVES[1].balances))

        self.assertEqual(proof[1].side, Side.RIGHT)
        self.assertEqual(proof[1].hash.hex(), 'e73ef74ee86648217d17b8c852e9532a2cea9997dcc0dcfef2812925ffdf9d9d')
        self.assertEqual(proof[1].balances, dict({'BTC': Decimal('1.12100011'), 'ETH': Decimal('5.22463023')}))

class VerifyMerkleProof(unittest.TestCase):
    def setUp(self) -> None:
        # Use root from above test case
        self.root = Node(
            hash = b'\x8d]_N6\xb2\x83\xa2\x9c\xe0\xabw\xaf\x97\xa2\tk\t\x1e\xb6\xb8$\xfb\x15l\xaa\xcel\xef\xb4\xbaA',
            balance_dict = dict({'BTC': Decimal('1.12100014'), 'ETH': Decimal('5.34775053')})
        )
        self.proof_steps = [
            ProofStep(
                side = Side.RIGHT,
                hash = b'\xe6#\xden\x01\xfaj\x89$\xb7\x1d\xf3C\x1a\x89\xee/\x9a\xe9-\x80qA"\x08&\xfcI\x9c\x197\xe1',
                balances = dict({'BTC': Decimal('0.00000002'), 'ETH': Decimal('0.00000000')})
            ),
            ProofStep(
                side = Side.RIGHT, 
                hash = b'\xe7>\xf7N\xe8fH!}\x17\xb8\xc8R\xe9S*,\xea\x99\x97\xdc\xc0\xdc\xfe\xf2\x81)%\xff\xdf\x9d\x9d',
                balances = dict({'BTC': Decimal('1.12100011'), 'ETH': Decimal('5.22463023')})
            )
        ]

    def test_verify_proof_correctly(self):
        # When
        verify_merkle_proof(self.root, self.proof_steps, INIT_AUDIT_ID, INIT_LEAVES[0])

        # Then
        # No assertion should be raised

if __name__ == '__main__':
    unittest.main()