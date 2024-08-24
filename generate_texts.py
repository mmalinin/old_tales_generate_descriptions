import itertools
import os
import re
import sys
import xml.etree.ElementTree as ElementTree
from typing import Callable, Sequence

from data_model import PlayableItem, Config
from markdown_table import data_to_markdown_table
from wiki_table import data_to_wiki_table

game_name = "Deathless Tales of Old Rus"
config_file_name = "config.xml"
loc_file_ru = "locale_ru.xml"

__environ_path = "PATH"

__dummy_hero = "HERO_DUMMY_UNIT_TEST"

## [TERM_ETHER:Spectral]. [TERM_UNPLAYABLE:Unplayable]. Lose 1 [ICON_ENERGY] when this card appears in your hand.]
__re_process_inline = re.compile(r"\[(.+):(.+)]")

__nbsp = "\xA0"

loc_ru = {
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





def parse_loc_file(file_path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    xml = ElementTree.parse(file_path)
    for child in xml.getroot():
        result[child.attrib["key"]] = child.text
    return result


def process_loc_string(locstr: str, energy_str) -> str:
    proc = locstr.replace(__nbsp, ' ')
    proc = proc.replace("[ICON_ENERGY]", energy_str)
    proc = __re_process_inline.sub(lambda m: f"<{m.group(2)}>", proc)
    return proc


def safe_localize(loc_text: str, loc: dict[str, str]):
    if loc_text is None:
        return ""

    if loc_text not in loc:
        return loc_text

    return loc[loc_text] if loc_text else ""


def generate_markdown_table(items: list[PlayableItem],
                            get_item_header: Callable[[], Sequence[str]],
                            item_to_row: Callable[[PlayableItem], Sequence[str]],
                            item_type_str: str, loc: dict[str, str]) -> list[str]:
    result: list[str] = []

    def item_sort_key(x: PlayableItem):
        return -x.quality, loc[x.name], safe_localize(x.related_hero, loc)

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


def generate_wiki_table(items: list[PlayableItem],
                        get_item_header: Callable[[], Sequence[str]],
                        item_to_row: Callable[[PlayableItem], Sequence[str]]) -> list[str]:
    header = get_item_header()
    rows: list[list[str]] = [header]

    for item in items:
        rows.append(list(item_to_row(item)))

    return data_to_wiki_table(rows, remove_empty_columns=True)


def process_items(items: list[PlayableItem], type_header: str, loc: dict[str, str]) -> tuple[list[str], list[str]]:
    def item_sort_key(x: PlayableItem):
        return -x.quality, loc[x.name], safe_localize(x.related_hero, loc)

    sorted_items = sorted(items, key=item_sort_key, reverse=False)

    # markdown is split into rarity sections
    def markdown_get_item_header():
        return [loc['_name_'], loc['_func_'], loc['_src_'], loc['_hero_']]

    def markdown_item_to_row(item: PlayableItem):
        return [loc[item.name], process_loc_string(loc[item.descr], loc['_nrg_']),
                safe_localize(item.get_item_source_loc(), loc), safe_localize(item.related_hero, loc)]

    markdown: list[str] = [f"# {type_header}"]
    type_str = sorted_items[0].get_item_type_str()
    markdown += generate_markdown_table(sorted_items, markdown_get_item_header, markdown_item_to_row, type_str, loc)

    # wiki is just a raw table
    def wiki_get_item_header():
        return [loc['_name_'], loc['_func_'], loc['_qty_'], loc['_src_'], loc['_hero_']]

    def wiki_item_to_row(item: PlayableItem):
        return [loc[item.name], process_loc_string(loc[item.descr], loc['_nrg_']),
                str(item.quality) + " " + loc[f"{type_str}_{item.quality}"],
                safe_localize(item.get_item_source_loc(), loc), safe_localize(item.related_hero, loc)]

    wiki = generate_wiki_table(sorted_items, wiki_get_item_header, wiki_item_to_row)

    return markdown, wiki

def default_sorting_fn(x: PlayableItem):
    return -x.quality, x.name,


def generate_texts(path):
    folder = path

    if folder is None:
        print("Could not find game installation folder.")
        exit(1)
    
    if not os.path.exists(os.path.join(folder, config_file_name)):
        print(f"Could not find {config_file_name} in the game folder.")
    
    print("Parsing config.xml...")
    config_xml = ElementTree.parse(os.path.join(folder, config_file_name))
    config = Config(config_xml.getroot())

    print("Parsing locale.xml...")
    loc = {}
    loc.update(loc_ru)  # set up special string for headers and stuff
    loc.update(parse_loc_file(os.path.join(folder, loc_file_ru)))

    # filter out any test and dummy heroes
    only_real_heroes = set(filter(lambda x: x.is_hero and x.key != __dummy_hero and "_TEST" not in x.key, config.units))

    # prepare hero unit names for relic relations
    for unit in filter(lambda x: x in only_real_heroes, config.units):
        loc[unit.key] = loc[unit.name]

    # prepare hero name filters
    only_real_hero_names = set(map(lambda x: x.key, only_real_heroes))


    only_visible_relics = filter(lambda  x: not x.hidden, config.relics)
    # remove dummy relics
    only_real_relics = list(
        filter(lambda x: True if x.related_hero is None else x.related_hero in only_real_hero_names, only_visible_relics))
    relics = sorted(only_real_relics, key=default_sorting_fn)

    # remove dummy consumables
    only_real_consumables = list(
        filter(lambda x: True if x.related_hero is None else x.related_hero in only_real_hero_names,
               config.consumables))
    consumables = sorted(only_real_consumables, key=default_sorting_fn)

    print("Processing relics and consumables...")

    if not os.path.exists("output"):
        os.mkdir("output")

    (relic_markdown, relic_wiki) = process_items(relics, "Relics", loc)
    with open(os.path.join("output", "relics.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(relic_markdown))

    with open(os.path.join("output", "relics_wiki.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(relic_wiki))

    (consumables_markdown, consumables_wiki) = process_items(consumables, "Consumables", loc)
    with open(os.path.join("output", "consumables.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(consumables_markdown))

    with open(os.path.join("output", "consumables_wiki.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(consumables_wiki))

    print("Done!")


if __name__ == '__main__':
    
    path = ''
    if __environ_path in os.environ and os.path.exists(os.path.join(os.environ[__environ_path], config_file_name)):
        path = os.environ[__environ_path]
        print(f"Find config path from environment variable {__environ_path}")
        
    if sys.argv and os.path.exists(os.path.join(sys.argv[0], config_file_name)):
        path = sys.argv[0]
        print(f"Find config path from command line argument {sys.argv[0]}")
        
    if not path:
        print("Config path not found")
        exit(1)
    generate_texts(path)
