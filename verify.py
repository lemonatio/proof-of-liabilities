import csv
from lib.merkle import verify_merkle_proof_from_leaf, to_decimal_balance, Node, ProofStep, Side
import argparse
import re
import json
import hashlib
import time 
import itertools
import threading
import time

def animate():
    timeout = 0.2
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        
        print(f"\rVerifying {c}", flush=True, end="")
        time.sleep(timeout)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Relative path to the input file', required = True)
    parser.add_argument('-v', '--variables', help='Relative path to json file with needed variables', required = True)

    args = parser.parse_args()
    
    return args.input, args.variables

def decode_balance(balance_str: str) -> dict[str, str]:
    new_balance_list: list[tuple[str, str]] = []

    # If leaf has no balances then return an empty dict
    if (balance_str == ""): return dict()

    balance_list_splitted = balance_str.split('|')
    for balance in balance_list_splitted:
        splitted_balance = balance.split(':')
        if float(splitted_balance[1]) < 0: raise Exception("User balance must be positive")

        new_balance_list.append((splitted_balance[0], splitted_balance[1]))

    filtered_balance_list = list(filter(lambda balance: not float(balance[1]) == 0, new_balance_list))
    return { balance[0]: balance[1] for balance in filtered_balance_list }

def to_proofstep_list(proof_list_str: str) -> list[ProofStep]:
    proof_list = list(map(lambda proof_step: proof_step.split(','), re.findall(r'\{(.*?)\}', proof_list_str)))
    return [ProofStep(Side[proof[0]], bytes.fromhex(proof[1]), to_decimal_balance(decode_balance(proof[2]))) for proof in proof_list]

def get_variables(filename: str):
    with open(filename) as f:
        return json.load(f)

done = False
if __name__ == '__main__':
    input_path, variables_path = parse_arguments()

    with open(input_path, 'r+') as file:
        variable_dict = get_variables(variables_path)
        reader = csv.DictReader(file)

        root_balances = variable_dict['root_balances']
        root_hash = variable_dict['root_hash']
        hash_function = getattr(hashlib, variable_dict['hash_algorithm'])
        
        for row in reader:
            # Expects file with header
            # id, balances, proof, audit_id

            id = row['id'].strip()
            audit_id = row['audit_id'].strip()
            merkle_leaf_hash = hash_function(str.encode(audit_id + id)).digest().hex()
            balances = to_decimal_balance(decode_balance(row['balances'].strip()))
            proof = to_proofstep_list(row['proof'].strip())

            try:
                t = threading.Thread(target=animate)
                t.start()

                time.sleep(1)
                print("\n")
                obtained_hash, obtained_balances = verify_merkle_proof_from_leaf(
                    Node(bytes.fromhex(root_hash), to_decimal_balance(decode_balance(root_balances))),
                    proof,
                    Node(bytes.fromhex(merkle_leaf_hash), balances)
                )

                print(f"\nObtained hash: \t{obtained_hash}")
                print(f"Root hash: \t{root_hash}")

                print(f"\nObtained balances: {obtained_balances}")
                print(f"Root balances: {root_balances}")

                print("\nVerified correctly!\n")
            except Exception as e:
                print(f"\nAn error ocurred when trying to verify: {e}")
            finally:
                done = True