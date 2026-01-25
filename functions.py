from db import get_list
from crypt import cipher
from settings import ENCODE

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
