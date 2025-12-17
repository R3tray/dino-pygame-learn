
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.env_util import make_vec_env
from config import Config
import os

def create_ppo_model(env, tensorboard_log=None, verbose=1):
    """
    Creates or loads a PPO model.
    """
    
    # Network Architecture (NatureCNN is default for CnnPolicy in SB3)
    policy_kwargs = dict(
        net_arch=dict(pi=[512], vf=[512]) # Customizing if needed, but NatureCNN is standard
    )
    
    model = PPO(
        "CnnPolicy",
        env,
        n_steps=Config.N_STEPS,
        batch_size=Config.BATCH_SIZE,
        learning_rate=Config.LEARNING_RATE,
        ent_coef=Config.ENT_COEF,
        clip_range=Config.CLIP_RANGE,
        gamma=Config.GAMMA,
        gae_lambda=Config.GAE_LAMBDA,
        tensorboard_log=tensorboard_log,
        verbose=verbose,
        device="cuda" # Force GPU as requested (RTX 3070Ti)
    )
    
    return model

def load_ppo_model(path, env=None):
    return PPO.load(path, env=env)
