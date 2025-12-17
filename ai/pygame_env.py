
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import cv2
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

# Import Game from dino-pygame
# We insert at 0 to prioritize finding 'main' inside dino-pygame over the root main.py
game_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dino-pygame'))
if game_path not in sys.path:
    sys.path.insert(0, game_path)

# Now we can import main, but we should be careful. 
# It's better to import the module object to verify it's the right one, 
# but simply prioritizing path usually works.
from main import Game, MS_PER_FRAME

# Cleanup path to avoid side effects for other modules
try:
    sys.path.remove(game_path)
except ValueError:
    pass

class DinoPygameEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self):
        super(DinoPygameEnv, self).__init__()
        
        # Initialize Game
        # human_mode=False disables the window popup if we implement that logic properly, 
        # but for now we might want to see it or use SDL_VIDEODRIVER=dummy
        self.game = Game(human_mode=True) 
        
        # Actions: 0: Do Nothing, 1: Jump, 2: Duck
        self.action_space = spaces.Discrete(3)
        
        # Observations: Grayscale 84x84
        # Shape: (84, 84, 1)
        self.observation_space = spaces.Box(
            low=0, high=255, 
            shape=(Config.TARGET_HEIGHT, Config.TARGET_WIDTH, 1), 
            dtype=np.uint8
        )
        
        self.frame_skip = 4

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.game.restart()
        # Ensure game is in playing state (start running)
        self.game.step(1) # Jump to start
        
        observation = self._get_observation()
        info = {}
        return observation, info

    def step(self, action):
        total_reward = 0
        terminated = False
        truncated = False
        info = {}
        
        # Frame Skipping
        for _ in range(self.frame_skip):
            state = self.game.step(action)
            
            # Accumulate reward
            step_reward = 0
            if state['crashed']:
                step_reward = Config.REWARD_DEATH
                terminated = True
            else:
                step_reward += Config.REWARD_ALIVE
                step_reward += Config.REWARD_VELOCITY_MULTIPLIER * state['speed']
                if action != 0:
                    step_reward += Config.REWARD_SPARSITY
            
            total_reward += step_reward
            
            if terminated:
                break
        
        observation = self._get_observation()
        info['score'] = state['score']
        
        return observation, total_reward, terminated, truncated, info

    def _get_observation(self):
        # 1. Get raw frame from game (H, W, 3)
        frame = self.game.get_frame()
        
        # 2. Preprocessing
        # Resize to 84x84
        resized = cv2.resize(frame, (Config.TARGET_WIDTH, Config.TARGET_HEIGHT), interpolation=cv2.INTER_AREA)
        
        # Grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        
        # Add channel dimension (H, W, 1)
        final_obs = np.expand_dims(gray, axis=-1)
        
        return final_obs.astype(np.uint8)

    def render(self, mode='human'):
        # Game class handles rendering to screen in step()
        pass

    def close(self):
        import pygame
        pygame.quit()
