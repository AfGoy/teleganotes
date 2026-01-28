from db import get_list
from crypt import cipher
from settings import ENCODE, GROQ_API_KEY
import aiohttp

async def fetch_groq_data(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 1,
        "max_tokens": 1024,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"Error fetching Groq data: {response.status}")
                return "Error fetching Groq data"

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
