import hashlib


def calculate_md5(content):
    if isinstance(content, str):
        content = content.encode()
    md5_hash = hashlib.md5(content)
    return md5_hash.hexdigest()
