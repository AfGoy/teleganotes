from settings import ENCODE, GROQ_API_KEY
import aiohttp
import asyncio

class Client:
    def __init__(self, url: str, api_key: str,):
        self.url = url
        self.api_key = api_key

        self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
        }

        self.timeout = aiohttp.ClientTimeout(total=30)


    async def post(self, router: str, payload: dict):
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
                async with session.post(self.url + router, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    return f"Error: {response.status}"
                
        except asyncio.TimeoutError:
            return "Error: Request timed out"
        
        except aiohttp.ClientResponseError as e:
            return f"❌ HTTP ошибка: {e.status}"

        except aiohttp.ClientError as e:
            return f"❌ Ошибка клиента: {e}"