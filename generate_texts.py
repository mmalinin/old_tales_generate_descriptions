import itertools
import os
import sys
import xml.etree.ElementTree as ElementTree
from typing import Callable, Sequence, Dict

from locale import Locale
from data_model import PlayableItem, Config
from markdown_table import data_to_markdown_table
from table_utils import data_to_wiki_table

game_name = "Deathless Tales of Old Rus"
config_file_name = "config.xml"
loc_file_ru = "locale_ru.xml"

__environ_path = "GAME_CONFIG_PATH"

__nbsp = "\xA0"

loc_ru: dict[str, str] = {
    "": "",
    '_name_': "Название",
    '_func_': "Эффект",
    '_qty_': "Редкость",
    '_src_': "Источник",
    '_hero_': "Герой",
    '_nrg_': "энергии",
    '_event_': "Событие",
    '_reward_': "Награда",
    '_shop_': "Магазин",
    '_boss_': "Босс"
}


def items_to_markdown_table(items: list[PlayableItem],
                            get_item_header: Callable[[], Sequence[str]],
                            item_to_row: Callable[[PlayableItem], Sequence[str]],
                            item_type_str: str, loc: Locale) -> list[str]:
    result: list[str] = []

    def item_sort_key(x: PlayableItem):
        return -x.quality, loc[x.name], loc[x.related_hero]

    items.sort(key=item_sort_key, reverse=False)

    rows: list[list[str]] = []
    for k, group in itertools.groupby(items, lambda x: -x.quality):
        item_type_loc = loc[f"{item_type_str}_{-k}"]
        result.append(f"## {item_type_loc}")

        header = list(get_item_header())
        rows.append(header)
        for v in group:
            rows.append(list(item_to_row(v)))

        table = data_to_markdown_table(rows, remove_empty_columns=True)
        result += table
        rows.clear()
        result.append("")

    return result


def items_to_wiki_table(items: list[PlayableItem],
                        get_item_header: Callable[[], Sequence[str]],
                        item_to_row: Callable[[PlayableItem], Sequence[str]]) -> list[str]:
    header = get_item_header()
    rows: list[list[str]] = [header]

    for item in items:
        rows.append(list(item_to_row(item)))

    return data_to_wiki_table(rows, remove_empty_columns=True)


def process_markdown(sorted_items, loc, type_header) -> list[str]:
    type_str = sorted_items[0].get_item_type_str()

    # markdown is split into rarity sections
    def markdown_get_item_header():
        return [loc['_name_'],
                loc['_func_'],
                loc['_src_'],
                loc['_hero_']]

    def markdown_item_to_row(item: PlayableItem):
        return [loc[item.name],
                loc.process(item.descr),
                loc[item.get_item_source_loc()],
                loc[item.related_hero]]

    markdown: list[str] = [f"# {type_header}"]
    markdown += items_to_markdown_table(sorted_items, markdown_get_item_header, markdown_item_to_row, type_str, loc)
    return markdown


def process_wiki(sorted_items: list[PlayableItem], loc: Locale) -> list[str]:
    type_str = sorted_items[0].get_item_type_str()

    # wiki is just a raw table
    def wiki_get_item_header():
        return [loc['_name_'],
                loc['_func_'],
                loc['_qty_'],
                loc['_src_'],
                loc['_hero_']]

    def wiki_item_to_row(item: PlayableItem):
        return [loc[item.name],
                loc.process(item.descr),
                # add quality as a number for better sorting support
                str(item.quality) + " " + loc[f"{type_str}_{item.quality}"],
                loc[item.get_item_source_loc()],
                loc[item.related_hero]]

    wiki = items_to_wiki_table(sorted_items, wiki_get_item_header, wiki_item_to_row)
    return wiki


def process_items(items: list[PlayableItem], type_header: str, loc: Locale) -> tuple[list[str], list[str]]:
    def item_sort_key(x: PlayableItem):
        return -x.quality, loc[x.name], loc[x.related_hero]

    sorted_items = sorted(items, key=item_sort_key, reverse=False)

    markdown = process_markdown(sorted_items, loc, type_header)

    wiki = process_wiki(sorted_items, loc)

    return markdown, wiki


def write_items_to_files(items: list[PlayableItem], item_name: str, type_header: str, loc: Locale):
    (markdown, wiki) = process_items(items, type_header, loc)
    
    with open(os.path.join("output", f"{item_name}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(markdown))

    with open(os.path.join("output", f"{item_name}_wiki.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(wiki))
    

def load_locale(base_strings: Dict[str, str], loc_file_name: str):
    loc = Locale()

    # set up special string for headers and stuff
    loc.append_dict(base_strings)
    loc.append_xml(ElementTree.parse(loc_file_name))

    # special rules for processing descriptions
    loc.add_rule(__nbsp, ' ')
    loc.add_rule("[ICON_ENERGY]", loc["_nrg_"])
    return loc


def generate_texts(config_path):
    if config_path is None:
        print("Could not find game installation folder.")
        exit(1)

    if not os.path.exists(os.path.join(config_path, config_file_name)):
        print(f"Could not find {config_file_name} in the game folder.")

    print("Parsing config.xml...")
    config_xml = ElementTree.parse(os.path.join(config_path, config_file_name))
    config = Config(config_xml.getroot())

    print("Parsing locale.xml...")
    loc = load_locale(loc_ru, os.path.join(config_path, loc_file_ru))

    print("Processing relics and consumables...")
    # prepare hero unit names for relic relations
    for unit in filter(lambda x: x in config.only_real_heroes, config.units):
        loc[unit.key] = loc[unit.name]

    write_items_to_files(config.visible_relics, "relics", "Relics", loc)    
    write_items_to_files(config.visible_consumables, "consumables", "Consumables", loc)

    if not os.path.exists("output"):
        os.mkdir("output")

    print("Done!")


if __name__ == '__main__':

    path = ''
    if __environ_path in os.environ and os.path.exists(os.path.join(os.environ[__environ_path], config_file_name)):
        path = os.environ[__environ_path]
        print(f"Got config path from environment variable {__environ_path}")

    if sys.argv and os.path.exists(os.path.join(sys.argv[0], config_file_name)):
        path = sys.argv[0]
        print(f"Got config path from command line argument {sys.argv[0]}")

    if not path:
        print("Config path not found")
        exit(1)
    generate_texts(path)
