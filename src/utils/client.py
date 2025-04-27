from fireworks.client import Fireworks

def make_fw_client(api_key: str):
    return Fireworks(api_key=api_key)
