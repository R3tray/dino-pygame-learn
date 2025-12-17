
import argparse
import sys
import os

# Add tools to path if needed, though they are packages usually
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Project Raptor 2.0: Chrome Dino PPO Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Train Command
    train_parser = subparsers.add_parser("train", help="Start PPO training with 16 environments")

    # Tune Command
    tune_parser = subparsers.add_parser("tune", help="Run ROI tuner tool")
    
    # Play Command (Placeholder)
    play_parser = subparsers.add_parser("play", help="Run trained agent (not implemented yet)")

    args = parser.parse_args()

    if args.command == "train":
        print("Initializing Training Sequence...")
        from ai.training import train
        train()
    elif args.command == "tune":
        print("Initializing ROI Tuner...")
        from tools.roi_tuner import main as run_tuner
        run_tuner()
    elif args.command == "play":
        print("Play mode not implemented yet.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
