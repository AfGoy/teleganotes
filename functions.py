from db import get_list
from crypt import cipher
from settings import ENCODE, GROQ_API_KEY
import json
import aiohttp

def get_payload_from_json(filename):
    with open(filename, "r", encoding=ENCODE) as f:
        return json.load(f)


async def get_titles(owner):
    titles = []
    for i in await(get_list(owner)):
        titles.append(i[0])
    return titles

async def decode_list(list):
    list_decoded = []
    for coded in list:
        list_decoded.append(cipher.decrypt(coded).decode(ENCODE))
    return list_decoded
