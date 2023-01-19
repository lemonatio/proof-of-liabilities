import csv
from lib.merkle import MerkleSumTree, ProofStep, Leaf, Node, verify_merkle_proof
import argparse

def get_merkle_proofs(tree: MerkleSumTree, user_ids: list[str]) -> dict[str, list[ProofStep]]:
    proofs = {}

    for id in user_ids:
        proof = tree.get_proof(id)
        proofs[id] = proof

    return proofs

def verify_merkle_proofs(user_balances: list[Leaf], proofs: dict[str, list[ProofStep]], root_node: Node, audit_id: str):
    for user_balance in user_balances:
        verify_merkle_proof(root_node, proofs[user_balance.id], audit_id, user_balance)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Relative path to the input file', required = True)
    parser.add_argument('-o','--output',  nargs='+', help='Relative path for the output files. First path refers to the tree output, second path refers to the proofs output', required=True)
    parser.add_argument('-a','--audit_id',  help='Audit ID for this PoL audit')

    args = parser.parse_args()
    
    return args.input, args.output, args.audit_id

def decode_user_balance(user_balance: tuple[str, str]) -> Leaf:
    balance_str: str = user_balance[1]
    new_balance_list: list[tuple[str, str]] = []

    balance_list_splitted = balance_str.split('|')
    for balance in balance_list_splitted:
        splitted_balance = balance.split(':')
        if float(splitted_balance[1]) < 0: raise Exception("User balance must be positive")

        new_balance_list.append((splitted_balance[0], splitted_balance[1]))

    filtered_balance_list = list(filter(lambda balance: not float(balance[1]) == 0, new_balance_list))
    return Leaf(user_balance[0], { balance[0]: balance[1] for balance in filtered_balance_list })

if __name__ == '__main__':
    input_path, output_paths, audit_id = parse_arguments()

    with open(input_path, 'r+') as file:
        reader = csv.DictReader(file)

        encoded_user_balances: list[tuple[str, str]] = [(row['id'].strip(), row['balances'].strip()) for row in reader]
        user_balances: list[Leaf] = list(map(lambda user_balance: decode_user_balance(user_balance), encoded_user_balances))

        mst = MerkleSumTree(user_balances, hash_type = 'sha256', salt = audit_id.strip(), shuffle = True)

        proofs = get_merkle_proofs(mst, list(map(lambda ub: ub.id, user_balances)))

        verify_merkle_proofs(
            user_balances,
            proofs,
            mst.get_root(), 
            audit_id.strip()
        )
    
        with open(output_paths[0], 'w', newline='', encoding='utf-8') as write_file:
            writer = csv.writer(write_file)
            nodes = mst.get_nodes()

            for node in nodes:
                writer.writerow(node.to_string().split(','))

        with open(output_paths[1], 'w', newline='', encoding='utf-8') as write_file:
            writer = csv.writer(write_file)

            for proof in proofs.items():
                proof_map = map(lambda step: f"{{{step.to_string()}}}", proof[1])
                merkle_proof = f"[{','.join(proof_map)}]"

                writer.writerow([proof[0], merkle_proof])
                