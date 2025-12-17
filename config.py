import os

class Config:
    # --- Paths ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # --- Pygame Environment Config ---
    TARGET_WIDTH = 84
    TARGET_HEIGHT = 84
    FRAME_STACK = 4

    # --- PPO Hyperparameters ---
    N_ENVS = 1  # Start with 1 for Pygame stability
    N_STEPS = 4096 # Doubled from 2048
    BATCH_SIZE = 512
    LEARNING_RATE = 3e-4 
    ENT_COEF = 0.05 
    CLIP_RANGE = 0.2
    GAMMA = 0.99
    GAE_LAMBDA = 0.95
    TOTAL_TIMESTEPS = 1_000_000 

    # --- Rewards ---
    REWARD_ALIVE = 0.1
    REWARD_VELOCITY_MULTIPLIER = 0.02
    REWARD_OBSTACLE = 5.0
    REWARD_SPARSITY = -0.05
    REWARD_DEATH = -10.0