import hashlib

id = '00cf6625-9c3d-4e61-a17a-9820cae615cc'
audit_id = '123456'

# Using SHA256
hash = hashlib.sha256(str.encode(audit_id + id)).digest().hex()

print(f"Obtained merkle leaf hash: {hash}")