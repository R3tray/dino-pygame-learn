
import os
import time
import threading
import http.server
import socketserver
from stable_baselines3.common.vec_env import SubprocVecEnv, VecFrameStack, VecMonitor, DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback

from config import Config
from ai.env import DinoChromeEnv
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

# Helper to start local server silently
def start_server():
    os.chdir(os.path.join(Config.BASE_DIR, "dino-chrome"))
    handler = http.server.SimpleHTTPRequestHandler
    
    # Use ThreadingTCPServer to handle multiple browser requests concurrently
    class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        pass
        
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with ThreadingServer(("", 8000), handler) as httpd:
            print("Serving game at port 8000")
            httpd.serve_forever()
    except OSError: 
        print("Server likely already running on port 8000")

def make_env(env_id):
    def _init():
        env = DinoChromeEnv()
        env.env_id = env_id  # Override with correct ID
        return env
    return _init

class DebugScreenshotCallback(BaseCallback):
    """Callback to save debug screenshots after 10 seconds of training"""
    def __init__(self, logs_dir, delay_seconds=10, verbose=0):
        super().__init__(verbose)
        self.logs_dir = logs_dir
        self.delay_seconds = delay_seconds
        self.start_time = None
        self.screenshots_saved = False
        
    def _on_training_start(self):
        self.start_time = time.time()
        
    def _on_step(self):
        if not self.screenshots_saved and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.delay_seconds:
                self._save_screenshots()
                self.screenshots_saved = True
        return True
    
    def _save_screenshots(self):
        print(f"\n[Debug] Saving screenshots after {self.delay_seconds}s...")
        # Access the unwrapped environments
        try:
            vec_env = self.training_env
            # Get the base VecEnv (unwrap VecMonitor and VecFrameStack)
            while hasattr(vec_env, 'venv'):
                vec_env = vec_env.venv
            
            # For SubprocVecEnv, we need to use env_method
            if hasattr(vec_env, 'env_method'):
                vec_env.env_method('save_debug_screenshot', self.logs_dir)
            else:
                # DummyVecEnv
                for env in vec_env.envs:
                    env.save_debug_screenshot(self.logs_dir)
        except Exception as e:
            print(f"[Debug] Failed to save screenshots: {e}")

def train():
    # 0. Setup directories
    ensure_directories()
    
    # 1. Start HTTP Server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)

    # 2. Create Vectorized Environment
    cpu_count = Config.N_ENVS
    print(f"Starting {cpu_count} parallel environments...")
    
    if cpu_count == 1:
        env = DummyVecEnv([make_env(0)])
    else:
        env = SubprocVecEnv([make_env(i) for i in range(cpu_count)])
    
    # 3. Apply Wrappers
    env = VecFrameStack(env, n_stack=Config.FRAME_STACK)
    env = VecMonitor(env, filename=os.path.join(LOGS_DIR, "monitor"))

    # 4. Create Model
    model = create_ppo_model(env, tensorboard_log=TENSORBOARD_DIR)

    # 5. Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000, 
        save_path=CHECKPOINTS_DIR,
        name_prefix="dino_ppo"
    )
    
    debug_callback = DebugScreenshotCallback(LOGS_DIR, delay_seconds=10)

    # 6. Train
    print("Training started...")
    try:
        model.learn(
            total_timesteps=Config.TOTAL_TIMESTEPS, 
            callback=[checkpoint_callback, debug_callback]
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
