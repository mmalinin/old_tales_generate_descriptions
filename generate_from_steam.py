import os

from generate_texts import generate_texts, game_name, config_file_name
from steam_utils import find_game_path

__steam_game_data_folder = "Data/StreamingAssets/configs/xml"

if __name__ == '__main__':
    steam_root_path = find_game_path(game_name)
    if steam_root_path is None:
        print("Game not found in steam library")
        exit(1)

    game_config_path = os.path.join(steam_root_path, os.path.normpath(__steam_game_data_folder))

    if not os.path.exists(os.path.join(game_config_path, config_file_name)):
        print(f"Config file not found at {game_config_path}")
        exit(2)

    print(f"Using steam config path: {game_config_path}")
    generate_texts(game_config_path)