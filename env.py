import numpy as np
import gym
from gym import spaces
import time
import random

class FencingEnv(gym.Env):
    """
    Fencing Environment for Reinforcement Learning
    """
    
    # Define possible actions
    ACTIONS = {
        0: 'ADVANCE',
        1: 'RETREAT',
        2: 'LUNGE',
        3: 'FLECHE',
        4: 'PARRY_4',
        5: 'PARRY_6',
        6: 'NO_ACTION'
    }
    
    def __init__(self):
        super(FencingEnv, self).__init__()
        
        # Define action space
        self.action_space = spaces.Discrete(len(self.ACTIONS))
        
        # Define observation space
        # [left_pos, right_pos, left_blade_angle, right_blade_angle, 
        #  left_action_state, right_action_state, distance, time_remaining]
        self.observation_space = spaces.Box(
            low=np.array([-1, -1, 0, 0, 0, 0, 0, 0]),
            high=np.array([1, 1, 1, 1, 1, 1, 1, 1]),
            dtype=np.float32
        )
        
        # Environment parameters
        self.bout_duration = 30  # seconds
        self.start_time = None
        self.current_state = None
        self.scores = [0, 0]
        
        # Recovery times for actions (in seconds)
        self.recovery_times = {
            'ADVANCE': 0.2,
            'RETREAT': 0.2,
            'LUNGE': 0.5,
            'FLECHE': 0.7,
            'PARRY_4': 0.3,
            'PARRY_6': 0.3,
            'NO_ACTION': 0.1
        }
        
    def reset(self):
        """Reset the environment to initial state"""
        self.start_time = time.time()
        self.scores = [0, 0]
        
        # Initialize state
        self.current_state = {
            'left_fencer': {
                'position': -0.5,  # Normalized position on piste
                'blade_angle': 0.5,  # Normalized angle
                'current_action': None,
                'is_parrying': False,
                'recovery_time': 0
            },
            'right_fencer': {
                'position': 0.5,
                'blade_angle': 0.5,
                'current_action': None,
                'is_parrying': False,
                'recovery_time': 0
            },
            'distance': 1.0,
            'time_remaining': 1.0
        }
        
        return self._get_observation()
    
    def step(self, action):
        """Execute action and return new state, reward, done, info"""
        if self.current_state is None:
            raise Exception("Call reset() before step()")
            
        # Get action type
        action_type = self.ACTIONS[action]
        
        # Execute action and update state
        self._execute_action(action_type)
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check if episode is done
        done = self._is_done()
        
        # Get observation
        obs = self._get_observation()
        
        # Additional info
        info = {
            'scores': self.scores,
            'time_remaining': self._get_time_remaining(),
            'last_action': action_type
        }
        
        return obs, reward, done, info
    
    def _execute_action(self, action_type):
        """Update state based on action"""
        # Store previous distance for hit detection
        prev_distance = self.current_state['distance']
        
        # Get current positions and states
        left_pos = self.current_state['left_fencer']['position']
        right_pos = self.current_state['right_fencer']['position']
        
        # Movement amounts
        ADVANCE_AMOUNT = 0.1
        RETREAT_AMOUNT = 0.1
        LUNGE_AMOUNT = 0.3
        FLECHE_AMOUNT = 0.4
        
        # Handle different actions
        if action_type == 'ADVANCE':
            # Simple forward movement
            self.current_state['left_fencer']['position'] = min(1.0, left_pos + ADVANCE_AMOUNT)
            self.current_state['left_fencer']['current_action'] = 'ADVANCE'
            self.current_state['left_fencer']['is_parrying'] = False
            
        elif action_type == 'RETREAT':
            # Backward movement
            self.current_state['left_fencer']['position'] = max(-1.0, left_pos - RETREAT_AMOUNT)
            self.current_state['left_fencer']['current_action'] = 'RETREAT'
            self.current_state['left_fencer']['is_parrying'] = False
            
        elif action_type == 'LUNGE':
            # Forward attacking movement with extended blade
            self.current_state['left_fencer']['position'] = min(1.0, left_pos + LUNGE_AMOUNT)
            self.current_state['left_fencer']['current_action'] = 'LUNGE'
            self.current_state['left_fencer']['blade_angle'] = 0.8  # Extended blade
            self.current_state['left_fencer']['is_parrying'] = False
            
            # Check for hit
            if self._check_hit('LUNGE'):
                self.scores[0] += 1
                
        elif action_type == 'FLECHE':
            # Aggressive forward attack
            self.current_state['left_fencer']['position'] = min(1.0, left_pos + FLECHE_AMOUNT)
            self.current_state['left_fencer']['current_action'] = 'FLECHE'
            self.current_state['left_fencer']['blade_angle'] = 0.9  # Fully extended blade
            self.current_state['left_fencer']['is_parrying'] = False
            
            # Check for hit
            if self._check_hit('FLECHE'):
                self.scores[0] += 1
                
        elif action_type == 'PARRY_4':
            # Inside high line parry
            self.current_state['left_fencer']['current_action'] = 'PARRY_4'
            self.current_state['left_fencer']['blade_angle'] = 0.4
            self.current_state['left_fencer']['is_parrying'] = True
            
        elif action_type == 'PARRY_6':
            # Outside high line parry
            self.current_state['left_fencer']['current_action'] = 'PARRY_6'
            self.current_state['left_fencer']['blade_angle'] = 0.6
            self.current_state['left_fencer']['is_parrying'] = True
            
        elif action_type == 'NO_ACTION':
            # Reset blade angle to neutral
            self.current_state['left_fencer']['current_action'] = None
            self.current_state['left_fencer']['blade_angle'] = 0.5
            self.current_state['left_fencer']['is_parrying'] = False
        
        # Update distance
        self._update_distance()
        
        # Apply recovery time
        self.current_state['left_fencer']['recovery_time'] = self.recovery_times[action_type]
        
        # Simulate opponent response (simple rule-based)
        self._opponent_response(action_type, prev_distance)

    def _check_hit(self, attack_type):
        """
        Check if current action results in a hit
        Returns True if hit lands, False otherwise
        """
        # Get current state values
        distance = self.current_state['distance']
        opponent_parrying = self.current_state['right_fencer']['is_parrying']
        
        # Different hit conditions based on attack type
        if attack_type == 'LUNGE':
            # Lunge can score at medium distance if opponent isn't parrying
            hit_possible = distance < 0.4 and not opponent_parrying
            
        elif attack_type == 'FLECHE':
            # Fleche can score at slightly longer distance but is more committal
            hit_possible = distance < 0.5 and not opponent_parrying
            
        else:
            hit_possible = False
        
        # Random factor for realism (90% chance of hit if conditions are met)
        return hit_possible and random.random() < 0.9

    def _opponent_response(self, agent_action, prev_distance):
        """
        Simple rule-based opponent behavior
        """
        # Get current state
        distance = self.current_state['distance']
        opponent_pos = self.current_state['right_fencer']['position']
        
        # Opponent behavior rules
        if agent_action in ['LUNGE', 'FLECHE']:
            # Attempt to parry if agent is attacking
            if random.random() < 0.6:  # 60% chance to parry
                self.current_state['right_fencer']['is_parrying'] = True
                self.current_state['right_fencer']['current_action'] = 'PARRY_4' if random.random() < 0.5 else 'PARRY_6'
            
        elif distance < 0.3:
            # Retreat if too close
            self.current_state['right_fencer']['position'] = min(1.0, opponent_pos + 0.1)
            self.current_state['right_fencer']['current_action'] = 'RETREAT'
            
        elif distance > 0.7:
            # Advance if too far
            self.current_state['right_fencer']['position'] = max(-1.0, opponent_pos - 0.1)
            self.current_state['right_fencer']['current_action'] = 'ADVANCE'
            
        else:
            # Occasionally attempt an attack
            if random.random() < 0.2:  # 20% chance to attack
                self.current_state['right_fencer']['position'] = max(-1.0, opponent_pos - 0.3)
                self.current_state['right_fencer']['current_action'] = 'LUNGE'
                
                # Check if opponent scores
                if not self.current_state['left_fencer']['is_parrying'] and distance < 0.4:
                    self.scores[1] += 1
        
        # Update distance after opponent move
        self._update_distance()
    
    def _calculate_reward(self):
        """Calculate reward based on current state"""
        reward = 0
        
        # Reward for scoring
        if self.scores[0] > 0:  # If left fencer (agent) scored
            reward += 1.0
        
        # Penalty for getting hit
        if self.scores[1] > 0:  # If right fencer scored
            reward -= 1.0
            
        # Small reward for maintaining good distance
        if 0.3 <= self.current_state['distance'] <= 0.7:
            reward += 0.01
            
        # Penalty for out of bounds
        if abs(self.current_state['left_fencer']['position']) > 1:
            reward -= 0.5
            
        return reward
    
    def _is_done(self):
        """Check if episode is done"""
        return (
            self._get_time_remaining() <= 0 or  # Time's up
            any(score > 0 for score in self.scores) or  # Point scored
            abs(self.current_state['left_fencer']['position']) > 1  # Out of bounds
        )
    
    def _get_observation(self):
        """Convert current state to observation array"""
        return np.array([
            self.current_state['left_fencer']['position'],
            self.current_state['right_fencer']['position'],
            self.current_state['left_fencer']['blade_angle'],
            self.current_state['right_fencer']['blade_angle'],
            float(self.current_state['left_fencer']['is_parrying']),
            float(self.current_state['right_fencer']['is_parrying']),
            self.current_state['distance'],
            self._get_time_remaining() / self.bout_duration
        ], dtype=np.float32)
    
    def _get_time_remaining(self):
        """Get remaining time in bout"""
        elapsed = time.time() - self.start_time
        return max(0, self.bout_duration - elapsed)
    
    def _update_distance(self):
        """Update distance between fencers"""
        left_pos = self.current_state['left_fencer']['position']
        right_pos = self.current_state['right_fencer']['position']
        self.current_state['distance'] = abs(right_pos - left_pos)

