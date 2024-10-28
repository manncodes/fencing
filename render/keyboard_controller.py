import asyncio
import aiohttp
import time
import logging
from pynput import keyboard
from typing import Dict
from asyncio import Queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FencingController:

    def __init__(self, server_url="http://127.0.0.1:8000"):
        self.server_url = server_url
        self.session = None
        self.running = False
        self.last_action_time: Dict[str, float] = {}
        self.throttle_delay = 0.1
        self.action_queue = Queue()

        # Action mapping for arrow keys (Player 2)
        self.action_map = {
            keyboard.Key.up: ('right', 'advance'),
            keyboard.Key.down: ('right', 'retreat'),
            keyboard.Key.left: ('right', 'step_left'),
            keyboard.Key.right: ('right', 'step_right'),
        }

        # Character key mapping
        self.char_action_map = {
            # Left Fencer (WASD + surrounding keys)
            'w': ('left', 'advance'),  # Forward
            's': ('left', 'retreat'),  # Back
            'a': ('left', 'step_left'),  # Left
            'd': ('left', 'step_right'),  # Right
            'q': ('left', 'parry_4'),  # Left parry
            'e': ('left', 'parry_6'),  # Right parry
            'r': ('left', 'lunge'),  # Forward attack
            'f': ('left', 'disengage'),  # Tactical move

            # Right Fencer (supplementary keys near arrow keys)
            'l': ('right', 'parry_4'),  # Left parry
            ';': ('right', 'parry_6'),  # Right parry
            'p': ('right', 'lunge'),  # Forward attack
            '/': ('right', 'disengage'),  # Tactical move
        }

    async def send_action(self, fencer: str, action: str):
        """Send action to the server"""
        if not self.session:
            return

        # Throttle check
        action_key = f"{fencer}_{action}"
        current_time = time.time()
        if action_key in self.last_action_time:
            if current_time - self.last_action_time[
                    action_key] < self.throttle_delay:
                return

        self.last_action_time[action_key] = current_time

        url = f"{self.server_url}/action/{fencer}/{action}"
        try:
            async with self.session.post(url) as response:
                if response.status == 200:
                    logger.info(f"Sent: {fencer} - {action}")
                else:
                    logger.error(f"Failed to send action: {response.status}")
        except Exception as e:
            logger.error(f"Error sending action: {e}")

    def on_press(self, key):
        """Handle key press events"""
        if not self.running:
            return

        # Check if it's a special key (arrow keys, etc.)
        if key in self.action_map:
            fencer, action = self.action_map[key]
            self.action_queue.put_nowait((fencer, action))
            return

        # Check if it's a character key
        try:
            char = key.char
            if char in self.char_action_map:
                fencer, action = self.char_action_map[char]
                self.action_queue.put_nowait((fencer, action))
        except AttributeError:
            pass

    def on_release(self, key):
        """Handle key release events"""
        if key == keyboard.Key.esc:
            self.running = False
            return False

    async def process_action_queue(self):
        """Process queued actions"""
        while self.running:
            try:
                fencer, action = await self.action_queue.get()
                await self.send_action(fencer, action)
                self.action_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing action: {e}")

    async def run(self):
        """Main run loop"""
        self.running = True

        # Print control instructions
        print("\nFencing Controller - Keyboard Controls:")
        print("\nLeft Fencer (WASD Layout):")
        print("W - Advance")
        print("S - Retreat")
        print("A - Step Left")
        print("D - Step Right")
        print("Q - Parry 4")
        print("E - Parry 6")
        print("R - Lunge")
        print("F - Disengage")

        print("\nRight Fencer (Arrow Keys):")
        print("↑ - Advance")
        print("↓ - Retreat")
        print("← - Step Left")
        print("→ - Step Right")
        print("L - Parry 4")
        print("; - Parry 6")
        print("P - Lunge")
        print("/ - Disengage")

        print("\nPress ESC to quit\n")

        try:
            # Set up aiohttp session
            async with aiohttp.ClientSession() as session:
                self.session = session

                # Start keyboard listener
                listener = keyboard.Listener(on_press=self.on_press,
                                             on_release=self.on_release)
                listener.start()

                # Start action queue processor
                queue_processor = asyncio.create_task(
                    self.process_action_queue())

                # Keep running until ESC is pressed
                while self.running:
                    await asyncio.sleep(0.01)

                # Cleanup
                queue_processor.cancel()
                await queue_processor
                listener.stop()

        except Exception as e:
            logger.error(f"Error in run loop: {e}")
        finally:
            self.running = False


def main():
    asyncio.run(FencingController().run())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nController stopped by user")
