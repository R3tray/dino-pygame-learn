
import os

class Config:
    # --- Paths ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    GAME_PATH = os.path.join(BASE_DIR, "dino-chrome", "index.html")
    # For local server, we might want to serve the dir. 
    # But usually just file:// works or we start http server.
    # Given the requirements, we'll use a local http server url.
    GAME_URL = "http://localhost:8000/index.html" 
    
    # --- Chrome / Selenium ---
    CHROME_DRIVER_PATH = "chromedriver" # Assumes in PATH
    WINDOW_WIDTH = 960
    WINDOW_HEIGHT = 540
    CHROME_ARGS = [
        "--no-sandbox",
        "--disable-gpu",
        "--mute-audio",
        f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}",
        "--disable-infobars",
        "--disable-notifications",
        # Critical for background execution on Windows/Linux without Xvfb
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        # "--headless=new" # Uncomment this to run invisible (faster, no occlusion issues)
    ]

    # --- CV Pipeline ---
    # Original screen is likely larger, but we resize window to 960x540.
    # We need to tune these values using roi_tuner.py.
    # Dino is usually near the bottom-left. 
    ROI_TOP = 120   # Moved down from 150 (approx middle-lower)
    ROI_LEFT = 50   # Keep left
    ROI_WIDTH = 1400 # Slightly wider
    ROI_HEIGHT = 500 # Keep height
    
    TARGET_WIDTH = 84
    TARGET_HEIGHT = 84
    FRAME_STACK = 4

    # --- PPO Hyperparameters ---
    N_ENVS = 4  # As requested
    N_STEPS = 2048
    BATCH_SIZE = 512
    LEARNING_RATE = 3e-4 # Linear decay can be implemented in training loop
    ENT_COEF = 0.05  # Increased from 0.01 to encourage exploration
    CLIP_RANGE = 0.2
    GAMMA = 0.99
    GAE_LAMBDA = 0.95
    TOTAL_TIMESTEPS = 1_000_000 

    # --- Rewards ---
    REWARD_ALIVE = 0.1
    REWARD_VELOCITY_MULTIPLIER = 0.02
    REWARD_OBSTACLE = 5.0
    REWARD_SPARSITY = -0.05
    REWARD_DEATH = -10.0  # Reduced from -100 to avoid overwhelming negative signal


    # --- System ---
    VNC_PORT = 5900 # For reference
