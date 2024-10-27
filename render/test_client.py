import aiohttp
import asyncio


async def test_actions():
    async with aiohttp.ClientSession() as session:
        # Test sequence
        actions = [("left", "advance"), ("left", "lunge"),
                   ("right", "parry_4"), ("right", "retreat")]

        for fencer, action in actions:
            url = f"http://127.0.0.1:8000/action/{fencer}/{action}"
            try:
                async with session.post(url) as response:
                    result = await response.json()
                    print(f"Sent {action} for {fencer}: {result}")
                await asyncio.sleep(1)  # Wait between actions
            except Exception as e:
                print(f"Error sending {action}: {e}")


if __name__ == "__main__":
    asyncio.run(test_actions())
