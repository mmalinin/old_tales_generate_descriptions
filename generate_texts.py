import itertools
import os
import re
import xml.etree.ElementTree as ElementTree

from typing import Callable, Iterable, Sequence

from data_model import Relic, PlayableItem, Config
from markdown_table import data_to_markdown_table
from steam_utils import find_game_path
from wiki_table import data_to_wiki_table

__game_name = "Deathless Tales of Old Rus"

__steam_game_data_folder = "Data/StreamingAssets/configs/xml"
__data_file = "config.xml"
__loc_file_ru = "locale_ru.xml"

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


def get_xml_file_path(steam_root_path: str, file_path: str):
    path = os.path.join(steam_root_path, os.path.normpath(__steam_game_data_folder), file_path)
    return path


def parse_loc_file(file_path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    xml = ElementTree.parse(file_path)
    for child in xml.getroot():
        result[child.attrib["key"]] = child.text
    return result


def gather_items(config: ElementTree.ElementTree, key: str) -> list[tuple[int, str, str]]:
    items: list[tuple[int, str, str]] = []

    for relic in config.findall(f".//{key}"):
        relic_elem_name = relic.find(".//visual//name")
        relic_elem_descr = relic.find(".//visual//desc")
        relid_elem_quality = relic.find(".//quality")
        if relic_elem_name is None or relic_elem_descr is None or relid_elem_quality is None:
            continue

        related_hero = relic.find(".//related_hero")
        if related_hero is not None and related_hero.text == __dummy_hero:
            continue

        items.append((int(relid_elem_quality.text), relic_elem_name.text, relic_elem_descr.text))

    items.sort(key=lambda x: x[0], reverse=False)
    return items


def process_loc_string(locstr: str, energy_str) -> str:
    proc = locstr.replace(__nbsp, ' ')
    proc = proc.replace("[ICON_ENERGY]", energy_str)
    proc = __re_process_inline.sub(lambda m: f"<{m.group(2)}>", proc)
    return proc


def process_item(item: PlayableItem, loc: dict[str, str]) -> (str, str):
    name = loc[item.name]
    desc = loc[item.descr]
    desc = process_loc_string(desc, loc['_nrg_'])
    return name, desc


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

    def markdown_item_to_row(relic: Relic):
        return [loc[relic.name], process_loc_string(loc[relic.descr], loc['_nrg_']),
                safe_localize(relic.get_item_source_loc(), loc), safe_localize(relic.related_hero, loc)]

    markdown: list[str] = [f"# {type_header}"]
    type_str = sorted_items[0].get_item_type_str()
    markdown += generate_markdown_table(sorted_items, markdown_get_item_header, markdown_item_to_row, type_str, loc)

    # wiki is just a raw table
    def wiki_get_item_header():
        return [loc['_name_'], loc['_func_'], loc['_qty_'], loc['_src_'], loc['_hero_']]

    def wiki_item_to_row(relic: Relic):
        return [loc[relic.name], process_loc_string(loc[relic.descr], loc['_nrg_']),
                str(relic.quality) + " " + loc[f"{type_str}_{relic.quality}"],
                safe_localize(relic.get_item_source_loc(), loc), safe_localize(relic.related_hero, loc)]

    wiki = generate_wiki_table(sorted_items, wiki_get_item_header, wiki_item_to_row)

    return markdown, wiki


def process_consumables(consumables: list[PlayableItem], loc: dict[str, str]) -> list[str]:
    result: list[str] = ["# Consumables"]
    result += generate_markdown_table(consumables, "CONSUMABLE_TYPE", loc)
    return result


def default_sorting_fn(x: PlayableItem):
    return -x.quality, x.name,


def run():
    folder = find_game_path(__game_name)

    if folder is None:
        print("Could not find game installation folder.")
        exit(1)

    print(f"Game found at path '{folder}'")

    print("Parsing config.xml...")
    config_xml = ElementTree.parse(get_xml_file_path(folder, __data_file))
    config = Config(config_xml.getroot())

    print("Parsing locale.xml...")
    loc = {}
    loc.update(loc_ru)  # set up special string for headers and stuff
    loc.update(parse_loc_file(get_xml_file_path(folder, __loc_file_ru)))

    # filter out any test and dummy heroes
    only_real_heroes = set(filter(lambda x: x.is_hero and x.key != __dummy_hero and "_TEST" not in x.key, config.units))

    # prepare hero unit names for relic reliations
    for unit in filter(lambda x: x in only_real_heroes, config.units):
        loc[unit.key] = loc[unit.name]

    # prepare hero name filters
    only_real_hero_names = set(map(lambda x: x.key, only_real_heroes))

    # remove dummy relics
    only_real_relics = list(
        filter(lambda x: True if x.related_hero is None else x.related_hero in only_real_hero_names, config.relics))
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

    # relic_text = process_consumables(consumables, loc)
    # with open("consumables.md", "w", encoding="utf-8") as f:
    #     f.write("\n".join(relic_text))

    print("Done!")


if __name__ == '__main__':
    run()
