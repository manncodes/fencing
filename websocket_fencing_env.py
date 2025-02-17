import numpy as np
import gym
from gym import spaces
import asyncio
import websockets
import json
import time
from datetime import datetime, timedelta

class WebSocketFencingEnv(gym.Env):
    """Fencing Environment that communicates with WebSocket server"""
    
    ACTIONS = {
        0: 'advance',
        1: 'retreat',
        2: 'lunge',
        3: 'fleche',
        4: 'parry_4',
        5: 'parry_6',
        6: 'disengage',
        7: 'no_action'
    }
    
    def __init__(self, websocket_url='ws://localhost:8000/ws', controlled_fencer='left'):
        super(WebSocketFencingEnv, self).__init__()
        self.websocket_url = websocket_url
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.controlled_fencer = controlled_fencer
        self.last_action_time = datetime.now()
        self.MIN_ACTION_INTERVAL = 0.1  # seconds
        
        print(f"Creating environment for {controlled_fencer} fencer")
        
        # Initialize state
        self.last_state = None
        self.scores = {'left': 0, 'right': 0}
        
        # Define action and observation spaces
        self.action_space = spaces.Discrete(len(self.ACTIONS))
        
        # Observation space: [left_pos, right_pos, left_blade, right_blade, distance]
        self.observation_space = spaces.Box(
            low=np.array([-7, -7, -np.pi, -np.pi, 0]),
            high=np.array([7, 7, np.pi, np.pi, 1]),
            dtype=np.float32
        )

    async def connect(self):
        """Connect to WebSocket server"""
        if not self.websocket:
            try:
                self.websocket = await websockets.connect(self.websocket_url)
                print(f"Connected to WebSocket server for {self.controlled_fencer} fencer")
                
                # Send initial hello message
                await self.websocket.send(json.dumps({
                    "type": "hello",
                    "fencer": self.controlled_fencer
                }))
                
                # Wait for initial state
                await self.get_state()
                
            except Exception as e:
                print(f"Connection error for {self.controlled_fencer} fencer: {e}")
                raise
    
    async def send_action(self, action):
        """Send action to WebSocket server"""
        if not self.websocket:
            print(f"No WebSocket connection for {self.controlled_fencer} fencer!")
            return
            
        # Rate limiting
        current_time = datetime.now()
        time_since_last = (current_time - self.last_action_time).total_seconds()
        if time_since_last < self.MIN_ACTION_INTERVAL:
            await asyncio.sleep(self.MIN_ACTION_INTERVAL - time_since_last)
        
        action_name = self.ACTIONS[action]
        if action_name != 'no_action':
            try:
                message = {
                    "type": "action",
                    "fencer": self.controlled_fencer,
                    "action": action_name
                }
                await self.websocket.send(json.dumps(message))
                print(f"Sent action {action_name} for {self.controlled_fencer} fencer")
                self.last_action_time = current_time
                
                # Small delay to allow action to take effect
                await asyncio.sleep(0.05)
                
            except Exception as e:
                print(f"Error sending action for {self.controlled_fencer} fencer: {e}")
    
    async def get_state(self):
        """Get current state from WebSocket server"""
        try:
            # Request state update
            await self.websocket.send(json.dumps({
                "type": "state_update",
                "fencer": self.controlled_fencer
            }))
            
            # Wait for response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
            data = json.loads(response)
            
            if data.get("type") == "state_response":
                state = data.get("state", {})
                self.last_state = state
                return state
                
        except Exception as e:
            print(f"Error getting state for {self.controlled_fencer} fencer: {e}")
            return None

    def reset(self):
        """Reset environment"""
        return self.loop.run_until_complete(self._async_reset())
    
    async def _async_reset(self):
        """Async reset implementation"""
        await self.connect()
        
        # Send reset command
        await self.websocket.send(json.dumps({
            "type": "reset",
            "fencer": self.controlled_fencer
        }))
        print(f"Sent reset command for {self.controlled_fencer} fencer")
        
        # Get initial state
        await self.get_state()
        return self._get_observation()
    
    def step(self, action):
        """Execute action and get new state"""
        return self.loop.run_until_complete(self._async_step(action))
    
    async def _async_step(self, action):
        """Async step implementation"""
        # Send action
        await self.send_action(action)
        
        # Get resulting state
        await self.get_state()
        
        # Process state into observation
        observation = self._get_observation()
        
        # Calculate reward and check if done
        reward, got_hit = self._calculate_reward()
        done = self._is_done()
        
        # Additional info
        info = {
            'scores': self.scores,
            'last_action': self.ACTIONS[action],
            '_calculate_reward': (reward, got_hit)
        }
        
        return observation, reward, done, info
    
    def _get_observation(self):
        """Convert raw state into normalized observation array"""
        if not self.last_state:
            return np.zeros(5, dtype=np.float32)
        
        try:
            # Get positions and normalize
            left_pos = float(self.last_state.get('left_position', -2)) / 7
            right_pos = float(self.last_state.get('right_position', 2)) / 7
            
            # Get blade angles and normalize
            left_blade = float(self.last_state.get('left_blade_angle', 0)) / np.pi
            right_blade = float(self.last_state.get('right_blade_angle', 0)) / np.pi
            
            # Convert distance to numerical value
            distance_map = {
                'INFIGHTING': 0.0,
                'SHORT': 0.25,
                'MEDIUM': 0.5,
                'LONG': 0.75,
                'OUT_OF_DISTANCE': 1.0
            }
            distance = distance_map.get(self.last_state.get('distance', 'LONG'), 0.75)
            
            if self.controlled_fencer == 'right':
                # Flip observations for right fencer
                left_pos, right_pos = -right_pos, -left_pos
                left_blade, right_blade = -right_blade, -left_blade
            
            return np.array([
                left_pos,
                right_pos,
                left_blade,
                right_blade,
                distance
            ], dtype=np.float32)
            
        except Exception as e:
            print(f"Error processing observation for {self.controlled_fencer} fencer: {e}")
            return np.zeros(5, dtype=np.float32)
    
    def _calculate_reward(self):
        """Calculate reward based on current state"""
        if not self.last_state:
            return 0.0, False
        
        reward = 0.0
        got_hit = False
        
        try:
            # Reward for scoring
            current_scores = {
                'left': self.last_state.get('left_score', 0),
                'right': self.last_state.get('right_score', 0)
            }
            
            if current_scores['left'] > self.scores['left']:
                if self.controlled_fencer == 'left':
                    reward += 1.0
                    got_hit = True
                else:
                    reward -= 1.0
            if current_scores['right'] > self.scores['right']:
                if self.controlled_fencer == 'right':
                    reward += 1.0
                    got_hit = True
                else:
                    reward -= 1.0
            
            self.scores = current_scores.copy()
            
            # Reward for maintaining good distance
            distance = self.last_state.get('distance', 'LONG')
            if distance in ['MEDIUM', 'SHORT']:
                reward += 0.01
            
            # Penalties for going outside piste
            left_pos = float(self.last_state.get('left_position', 0))
            right_pos = float(self.last_state.get('right_position', 0))
            
            if self.controlled_fencer == 'left':
                pos = left_pos
            else:
                pos = right_pos
                
            # Progressive penalty system:
            # - Small penalty when approaching boundary (>4 units)
            # - Medium penalty when near warning lines (>5 units)
            # - Large penalty when outside valid area (>6 units)
            # - Immediate end when way outside (>7 units)
            
            abs_pos = abs(pos)
            if abs_pos > 4:
                # Approaching boundary
                reward -= 0.05
            if abs_pos > 5:
                # Past warning lines
                reward -= 0.2
            if abs_pos > 6:
                # Outside valid area
                reward -= 0.5
            if abs_pos > 7:
                # Way outside - trigger done state
                reward -= 1.0
            
            # Small reward for moving towards opponent
            if self.controlled_fencer == 'left':
                if left_pos > self.last_state.get('prev_left_position', left_pos):
                    reward += 0.001
            else:
                if right_pos < self.last_state.get('prev_right_position', right_pos):
                    reward += 0.001
            
        except Exception as e:
            print(f"Error calculating reward for {self.controlled_fencer} fencer: {e}")
            
        return reward, got_hit
    
    def _is_done(self):
        """Check if episode is done"""
        if not self.last_state:
            return True
        
        try:
            # Episode is done if:
            # 1. A point was scored
            # 2. Fencer is out of bounds
            
            # Check scores
            if (self.last_state.get('left_score', 0) > 0 or 
                self.last_state.get('right_score', 0) > 0):
                return True
            
            # Check bounds - end episode if fencer goes way out of bounds
            if self.controlled_fencer == 'left':
                pos = float(self.last_state.get('left_position', 0))
            else:
                pos = float(self.last_state.get('right_position', 0))
                
            if abs(pos) > 7:  # Only end episode on severe boundary violations
                print(f"{self.controlled_fencer.upper()} fencer went far out of bounds! Position: {pos:.2f}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking done state for {self.controlled_fencer} fencer: {e}")
            return True
    
    def close(self):
        """Cleanup"""
        if self.websocket:
            self.loop.run_until_complete(self.disconnect())
            
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None