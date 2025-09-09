# cipher.py

def my_encrypt_block(block: str, key: str) -> str:
    rotated = ''.join(chr((ord(c) + ord(key[i % len(key)])) % 256) for i, c in enumerate(block))
    reversed_block = rotated[::-1]
    encrypted = ''.join(chr(ord(reversed_block[i]) ^ ord(key[i % len(key)])) for i in range(len(reversed_block)))
    return encrypted

def my_decrypt_block(block: str, key: str) -> str:
    xored = ''.join(chr(ord(block[i]) ^ ord(key[i % len(key)])) for i in range(len(block)))
    reversed_block = xored[::-1]
    decrypted = ''.join(chr((ord(reversed_block[i]) - ord(key[i % len(key)])) % 256) for i in range(len(reversed_block)))
    return decrypted

def encrypt_message(msg: str, key: str) -> str:
    blocks = [msg[i:i+16] for i in range(0, len(msg), 16)]
    return ''.join(my_encrypt_block(b.ljust(16, '\x00'), key) for b in blocks)

def decrypt_message(cipher: str, key: str) -> str:
    blocks = [cipher[i:i+16] for i in range(0, len(cipher), 16)]
    return ''.join(my_decrypt_block(b, key).rstrip('\x00') for b in blocks)
