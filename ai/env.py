
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import cv2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import io
import os
import base64
from PIL import Image

from config import Config

# Global counter for unique env IDs
_env_counter = 0
_env_counter_lock = None

def _get_next_env_id():
    global _env_counter
    current_id = _env_counter
    _env_counter += 1
    return current_id

class DinoChromeEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self):
        super(DinoChromeEnv, self).__init__()
        
        # Assign unique ID to this environment
        self.env_id = _get_next_env_id()
        
        # Stagger startup to avoid CPU/IO spike and Server overload
        time.sleep(random.uniform(1.0, 5.0))
        
        # Actions: 0: Do Nothing, 1: Jump, 2: Duck
        self.action_space = spaces.Discrete(3)
        
        # Observations: Grayscale 84x84
        self.observation_space = spaces.Box(
            low=0, high=255, 
            shape=(Config.TARGET_HEIGHT, Config.TARGET_WIDTH, 1), 
            dtype=np.uint8
        )

        self.driver = self._setup_driver()
        self.driver.get(Config.GAME_URL)
        
        # Wait for game to load
        time.sleep(2)
        
        self.is_ducking = False

        self.last_time_alive = 0
        self.current_speed = 0
        self.last_score = 0
        self._debug_saved = False
        
    def _setup_driver(self):
        chrome_options = Options()
        for arg in Config.CHROME_ARGS:
            chrome_options.add_argument(arg)
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def save_debug_screenshot(self, logs_dir):
        """Save debug screenshots: full screen with ROI box + scaled observation"""
        try:
            # 1. Capture full screenshot
            b64_img = self.driver.get_screenshot_as_base64()
            img_data = base64.b64decode(b64_img)
            nparr = np.frombuffer(img_data, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Draw ROI rectangle (green)
            x, y = Config.ROI_LEFT, Config.ROI_TOP
            w, h = Config.ROI_WIDTH, Config.ROI_HEIGHT
            cv2.rectangle(img_np, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(img_np, f"Env {self.env_id}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Save full screenshot with ROI
            full_path = os.path.join(logs_dir, f"env_{self.env_id}_full_roi.png")
            cv2.imwrite(full_path, img_np)
            
            # 2. Get scaled observation
            obs = self._get_observation()
            scaled_path = os.path.join(logs_dir, f"env_{self.env_id}_scaled_84x84.png")
            cv2.imwrite(scaled_path, obs)
            
            print(f"[Env {self.env_id}] Debug screenshots saved to {logs_dir}")
            self._debug_saved = True
        except Exception as e:
            print(f"[Env {self.env_id}] Failed to save debug screenshot: {e}")

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Ensure keys are released
        try:
             ActionChains(self.driver).key_up(Keys.DOWN).perform()
        except:
             pass
        self.is_ducking = False

        # Trigger reset in game
        try:
            # Check if crashed or not started
            crashed = self.driver.execute_script("return Runner.instance_ ? Runner.instance_.crashed : true")
            if crashed:
                self.driver.execute_script("Runner.instance_.restart()")
        except:
            # Fallback if specific runner instance not ready, usually reload
            self.driver.get(Config.GAME_URL)
            time.sleep(1)

        # CRITICAL: Press SPACE to actually start the game!
        time.sleep(0.3)
        ActionChains(self.driver).send_keys(Keys.SPACE).perform()
        time.sleep(0.2)  # Wait for game to start running
        
        self.last_score = 0
        self.current_speed = 0
        self.last_time_alive = time.time()
        
        observation = self._get_observation()
        info = {}
        return observation, info

    def step(self, action):
        # 1. Execute Action using Keyboard
        # Action map: 0: Nothing, 1: Jump, 2: Duck
        
        # Handle Ducking State (Hold Down Key)
        if action == 2:
            if not self.is_ducking:
                ActionChains(self.driver).key_down(Keys.DOWN).perform()
                self.is_ducking = True
        else:
            if self.is_ducking:
                ActionChains(self.driver).key_up(Keys.DOWN).perform()
                self.is_ducking = False
        
        # Handle Jump
        if action == 1:
            # Press Space (Tap)
            ActionChains(self.driver).send_keys(Keys.SPACE).perform()

        # 2. Get Game State (Done, Score, Speed) via JS
        try:
            game_state = self.driver.execute_script("""
                if (!Runner.instance_) return {crashed: false, distance: 0, speed: 0};
                return {
                    crashed: Runner.instance_.crashed,
                    distance: Runner.instance_.distanceRan,
                    speed: Runner.instance_.currentSpeed
                };
            """)
        except Exception:
            game_state = {'crashed': True, 'distance': 0, 'speed': 0}
        
        done = game_state['crashed']
        score = game_state['distance']
        self.current_speed = game_state['speed']
        
        # 3. Calculate Reward
        reward = 0
        
        if done:
            reward += Config.REWARD_DEATH
        else:
            reward += Config.REWARD_ALIVE
            reward += Config.REWARD_VELOCITY_MULTIPLIER * self.current_speed
            if action != 0:
                reward += Config.REWARD_SPARSITY
            
        # 4. Get Observation
        observation = self._get_observation()
        
        terminated = done
        truncated = False 
        info = {'score': score}
        
        return observation, reward, terminated, truncated, info

    def _get_observation(self):
        # 1. Capture screenshot
        b64_img = self.driver.get_screenshot_as_base64()
        image = Image.open(io.BytesIO(base64.b64decode(b64_img)))
        img_np = np.array(image)
        
        # 2. ROI Crop
        if len(img_np.shape) == 3 and img_np.shape[2] == 4:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
            
        roi = img_np[
            Config.ROI_TOP : Config.ROI_TOP + Config.ROI_HEIGHT,
            Config.ROI_LEFT : Config.ROI_LEFT + Config.ROI_WIDTH
        ]
        
        # 3. Preprocessing - Grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        
        # 4. Resize
        resized = cv2.resize(gray, (Config.TARGET_WIDTH, Config.TARGET_HEIGHT), interpolation=cv2.INTER_AREA)
        
        # Add channel dimension (H, W, 1)
        final_obs = np.expand_dims(resized, axis=-1)
        
        return final_obs

    def render(self, mode='human'):
        pass

    def close(self):
        if self.driver:
            self.driver.quit()
