import os
import time
from stable_baselines3.common.vec_env import SubprocVecEnv, VecFrameStack, VecMonitor, DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

from config import Config
from ai.pygame_env import DinoPygameEnv
from ai.model import create_ppo_model

# --- Directory Setup ---
LOGS_DIR = os.path.join(Config.BASE_DIR, "logs")
MODELS_DIR = os.path.join(Config.BASE_DIR, "ai", "models")
CHECKPOINTS_DIR = os.path.join(MODELS_DIR, "checkpoints")
TENSORBOARD_DIR = os.path.join(LOGS_DIR, "tensorboard")

def ensure_directories():
    """Create all required directories"""
    for dir_path in [LOGS_DIR, MODELS_DIR, CHECKPOINTS_DIR, TENSORBOARD_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    print(f"Directories ready: logs={LOGS_DIR}, models={MODELS_DIR}")

def make_env(env_id):
    def _init():
        env = DinoPygameEnv()
        return env
    return _init

def train():
    # 0. Setup directories
    ensure_directories()
    
    # 1. Create Vectorized Environment
    cpu_count = Config.N_ENVS
    print(f"Starting {cpu_count} environment(s)...")
    
    # Pygame might have issues with SubprocVecEnv on some systems (window management)
    # Using DummyVecEnv for single environment is safer and easier to debug
    if cpu_count == 1:
        env = DummyVecEnv([make_env(0)])
    else:
        env = SubprocVecEnv([make_env(i) for i in range(cpu_count)])
    
    # 2. Apply Wrappers
    env = VecFrameStack(env, n_stack=Config.FRAME_STACK)
    env = VecMonitor(env, filename=os.path.join(LOGS_DIR, "monitor"))

    # 3. Create Model
    model = create_ppo_model(env, tensorboard_log=TENSORBOARD_DIR)

    # 4. Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000, 
        save_path=CHECKPOINTS_DIR,
        name_prefix="dino_ppo"
    )
    
    # 5. Train
    print("Training started...")
    try:
        model.learn(
            total_timesteps=Config.TOTAL_TIMESTEPS, 
            callback=[checkpoint_callback]
        )
    except KeyboardInterrupt:
        print("Training interrupted.")
    finally:
        final_model_path = os.path.join(MODELS_DIR, "dino_ppo_final")
        model.save(final_model_path)
        env.close()
        print(f"Model saved to {final_model_path}")
        print("Environments closed.")

if __name__ == "__main__":
    train()