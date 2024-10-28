import asyncio
import aiohttp
import logging
from typing import List, Tuple
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FencingStrategy:

    def __init__(self):
        self.base_url = "http://localhost:8000/action"
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def execute_action(self, fencer: str, action: str) -> bool:
        """Execute a single fencing action"""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager.")

        try:
            url = f"{self.base_url}/{fencer}/{action}"
            async with self.session.post(url) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Success: {result}")
                    return True
                else:
                    text = await response.text()
                    logger.error(
                        f"Failed to execute action ({response.status}): {text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            return False

    async def execute_sequence(self, actions: List[Tuple[str, str, float]]):
        """Execute a sequence of actions with delays"""
        for fencer, action, delay in actions:
            logger.info(f"Executing: {fencer} {action}")
            success = await self.execute_action(fencer, action)
            if not success:
                logger.error(
                    f"Sequence stopped due to failed action: {fencer} {action}"
                )
                break
            await asyncio.sleep(delay)

    async def run_attack_sequence(self):
        """Example of an attack sequence"""
        sequence = [
            ("left", "advance", 1.0),
            ("left", "advance", 0.8),
            ("left", "lunge", 0.5),
        ]
        await self.execute_sequence(sequence)

    async def run_defense_sequence(self):
        """Example of a defense sequence"""
        sequence = [
            ("right", "retreat", 0.8),
            ("right", "parry_4", 0.3),
            ("right", "lunge", 0.5),
        ]
        await self.execute_sequence(sequence)


async def main():
    async with FencingStrategy() as strategy:
        try:
            logger.info("Starting attack sequence...")
            await strategy.run_attack_sequence()

            await asyncio.sleep(2)

            logger.info("Starting defense sequence...")
            await strategy.run_defense_sequence()

        except Exception as e:
            logger.error(f"Error in main sequence: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
