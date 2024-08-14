import os
import re
from winreg import *


def get_steam_root_folder():
    registry = ConnectRegistry(None, HKEY_LOCAL_MACHINE)

    try:
        with OpenKey(registry, "SOFTWARE\Wow6432Node\Valve\Steam") as k:
            install_path = QueryValueEx(k, "InstallPath")
    except FileNotFoundError as e:
        try:
            with OpenKey(registry, "SOFTWARE\Valve\Steam") as k:
                install_path = QueryValueEx(k, "InstallPath")
        except FileNotFoundError as e:
            install_path = None

    if (install_path is None) or (not os.path.exists(install_path[0])):
        return r"C:\Program Files (x86)\Steam"
    else:
        return install_path[0]


def find_steam_libraries():
    steam_config_path = os.path.join(get_steam_root_folder(), "config", "libraryfolders.vdf")

    if not os.path.exists(steam_config_path):
        print("Steam configuration file not found.")
        return []

    with open(steam_config_path, 'r') as file:
        contents = file.read()

    library_paths = re.findall(r'"path"\s+"([^"]+)"', contents)
    library_paths = list(map(lambda p: os.path.normpath(p), library_paths))

    return library_paths


def list_installed_games(library_paths):
    game_paths = []
    for path in library_paths:
        common_path = os.path.join(path, 'steamapps', 'common')
        if os.path.exists(common_path):
            game_paths.extend(map(lambda p: os.path.join(common_path, p), os.listdir(common_path)))

    return game_paths


def find_game_path(game_name):
    library_paths = find_steam_libraries()
    
    if library_paths is None:
        return None
    
    games_list = list_installed_games(library_paths)
    for game in games_list:
        if os.path.basename(game) == game_name:
            return game
    return None


if __name__ == '__main__':
    # Finding all Steam library paths
    lib_paths = find_steam_libraries()
    
    if lib_paths:
        print("Steam library paths found:")
        for path in lib_paths:
            print(path)
    
        # Listing installed games
        games = list_installed_games(lib_paths)
        print("\nInstalled games:")
        for game in games:
            print(game)
    else:
        print("No Steam library paths found.")