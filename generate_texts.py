import itertools
import os
import re
import xml.etree.ElementTree as ET

from steam_utils import find_game_path

__game_name = "Deathless Tales of Old Rus"

__steam_game_data_folder = "Data/StreamingAssets/configs/xml"
__data_file = "config.xml"
__loc_file_ru = "locale_ru.xml"

__dummy_hero = "HERO_DUMMY_UNIT_TEST"

## [TERM_ETHER:Spectral]. [TERM_UNPLAYABLE:Unplayable]. Lose 1 [ICON_ENERGY] when this card appears in your hand.]
__process_inline = re.compile(r"\[(.+):(.+)]")

__nbsp = "\xA0"


def get_xml_file_path(steam_root_path: str, file_path: str):
    path = os.path.join(steam_root_path, os.path.normpath(__steam_game_data_folder), file_path)
    return path


def parse_loc_file(file_path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    xml = ET.parse(file_path)
    for child in xml.getroot():
        result[child.attrib["key"]] = child.text
    return result


def process_loc_string(locstr: str, energy_str) -> str:
    proc = locstr.replace(__nbsp, ' ')
    proc = proc.replace("[ICON_ENERGY]", energy_str)
    proc = __process_inline.sub(lambda m: f"<{m.group(2)}>", proc)
    return proc


def gather_items(config: ET.ElementTree, key: str) -> list[(int, str, str)]:
    items: list[(int, str, str)] = []

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


def process_item(item: tuple[int, str, str], loc: dict[str, str]) -> (str, str):
    name = loc[item[1]]
    desc = loc[item[2]]
    desc = process_loc_string(desc, loc['_nrg_'])
    return (name, desc)


def process_items_group(items: list[tuple[int, str, str]], item_type_str: str, loc: dict[str, str]) -> list[str]:
    result: list[str] = []

    name_str = loc['_name_']
    func_str = loc['_func_']
    for k, group in itertools.groupby(items, lambda x: x[0]):
        relic_tupe_loc = loc[f"{item_type_str}_{k}"]
        result.append(f"## {relic_tupe_loc}")
        result.append(f"  | {name_str: <25} | {func_str} |")
        result.append(f"  | {':---': <25} | :--- |")
        for v in group:
            name, desc = process_item(v, loc)
            result.append(f"  | {name: <25} | {desc} |")
        result.append('')
    return result


def process_relics(config: ET.ElementTree, loc: dict[str, str]) -> list[str]:
    relics = gather_items(config, "relic")

    result: list[str] = ["# Relics"]
    result += process_items_group(relics, "RELIC_TYPE", loc)
    return result


def process_consumables(config: ET.ElementTree, loc: dict[str, str]) -> list[str]:
    consumables = gather_items(config, "consumable")

    result: list[str] = ["# Consumables"]
    result += process_items_group(consumables, "CONSUMABLE_TYPE", loc)
    return result


def run():
    folder = find_game_path(__game_name)
    
    if folder is None:
        print("Could not find game installation folder.")
        exit(1)
        
    print(f"Game found at path '{folder}'")
    
    loc = parse_loc_file(get_xml_file_path(folder, __loc_file_ru))

    config = ET.parse(get_xml_file_path(folder, __data_file))

    loc['_name_'] = "Имя"
    loc['_func_'] = "Эффект"
    loc['_nrg_'] = "энергии"

    print("Processing relics and consumables...")

    relic_text = process_relics(config, loc)
    with open("relics.md", "w", encoding="utf-8") as f:
        f.write("\n".join(relic_text))

    relic_text = process_consumables(config, loc)
    with open("consumables.md", "w", encoding="utf-8") as f:
        f.write("\n".join(relic_text))

    print("Done!")

if __name__ == '__main__':
    run()