
import argparse
import sys
import os

# Add tools to path if needed, though they are packages usually
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Project Raptor 2.0: Pygame Dino PPO Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Train Command
    train_parser = subparsers.add_parser("train", help="Start PPO training")

    # Play Command
    play_parser = subparsers.add_parser("play", help="Play the game manually")

    args = parser.parse_args()

    if args.command == "train":
        print("Initializing Training Sequence...")
        from ai.training import train
        train()
    elif args.command == "play":
        print("Launching Game for Human Play...")
        # Add dino-pygame to path so we can import main
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dino-pygame"))
        from main import Game
        game = Game(human_mode=True)
        game.run()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
