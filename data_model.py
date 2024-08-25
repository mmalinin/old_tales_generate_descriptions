import xml.etree.ElementTree as ElementTree
from enum import Enum
from typing import TypeVar

_dummy_hero = "HERO_DUMMY_UNIT_TEST"


def safe_get_text(element: ElementTree.Element, path: str, default: str = None) -> str | None:
    elem_node = element.find(path)
    return elem_node.text if elem_node is not None else default


def safe_get_int(element: ElementTree.Element, path: str, default: int = None) -> int | None:
    value = safe_get_text(element, path)
    return int(value) if value is not None else default


class BaseItem:
    def __init__(self, element: ElementTree.Element):
        self.name = safe_get_text(element, ".//visual//name")
        self.descr = safe_get_text(element, ".//visual//desc")
        self.key = element.attrib.get("key")


class ItemQuality(Enum):
    NORMAL = 0
    UNUSUAL = 1
    RARE = 2
    EPIC = 3
    LEGENDARY = 4
    MYTHIC = 5
    SET = 6
    FABLE = 7
    UNIQUE = 8
    HIDDEN = 9


class PlayableItem(BaseItem):
    def __init__(self, element: ElementTree.Element):
        super().__init__(element)
        self.quality = safe_get_int(element, ".//quality", -1)
        self.related_hero = safe_get_text(element, ".//related_hero")
        self.quality_str = f"{self.get_item_type_str()}_{self.quality}" if self.get_item_type_str() else None
        self.source = safe_get_int(element, ".//source")
        self.flag: bool = element.find(".//flags") is not None
        self.hidden = any(child.tag == "hidden_flag" for child in element)

    def get_item_type_str(self):
        return "PLAYABLE_ITEM_TYPE"

    def get_item_source_name(self):
        if self.source == 0:
            if self.flag:
                return "event"
            else:
                return "reward"
        elif self.source == 1:
            return "shop"
        elif self.source == 2:
            return "event"
        elif self.source == 3:
            return "boss"

    def get_item_source_loc(self):
        return f"_{self.get_item_source_name()}_" if self.source is not None else ""


class Relic(PlayableItem):
    def get_item_type_str(self):
        return "RELIC_TYPE"


class Consumable(PlayableItem):
    def get_item_type_str(self):
        return "CONSUMABLE_TYPE"


class Card(PlayableItem):
    class CardType(Enum):
        ATTACK = 1
        SKILL = 2
        POWER = 3
        STATUS = 4
        CURSE = 5

    def __init__(self, element: ElementTree.Element):
        super().__init__(element)
        self.cost = safe_get_int(element, ".//cost")
        self.upgrade = safe_get_text(element, ".//upgrade")
        self.card_type = safe_get_int(element, ".//type")
        
        damage_val = element.find(".//*damage")
        self.damage = damage_val.attrib.get("value") if damage_val is not None else None
    
        armor_val = element.find(".//*add_armor")
        self.armor = armor_val.attrib.get("value") if armor_val is not None else None
        
        self.is_mob = element.find(".//visual//intention") is not None or "_MOB_" in self.key

    def get_item_type_str(self):
        return "CARD_TYPE"

    def get_card_type_name(self):
        if self.card_type is not None:
            type_u = Card.CardType(self.card_type)
            return f"{self.get_item_type_str()}_{type_u.name}"


class Unit(BaseItem):
    def __init__(self, element: ElementTree.Element):
        super().__init__(element)
        self.hp = safe_get_int(element, ".//hp")
        self.attack = safe_get_int(element, ".//attack")
        self.armor = safe_get_int(element, ".//armor")
        self.nickname = safe_get_text(element, ".//visual//nickname")
        self.is_hero = element.find(".//type//hero") is not None


def default_item_sorting_fn(x: PlayableItem):
    return -x.quality, x.key


TPI = TypeVar("TPI", bound=PlayableItem)


class Config:
    def __init__(self, root: ElementTree.Element):
        self.relics: list[Relic] = []
        self.consumables: list[Consumable] = []
        self.cards: list[Card] = []
        self.units: list[Unit] = []
        self._load_items(root)
        self._process_items()

    def _load_items(self, root: ElementTree.Element):
        for element in root:
            if element.tag == "relic":
                self.relics.append(Relic(element))
            elif element.tag == "consumable":
                self.consumables.append(Consumable(element))
            elif element.tag == "card":
                self.cards.append(Card(element))
            elif element.tag == "unit":
                self.units.append(Unit(element))
        pass

    @staticmethod
    def _extract_visible_items(items: list[TPI], only_real_hero_names: set[str]) -> list[TPI]:
        only_visible_items = list(filter(lambda x: not x.hidden, items))
        only_visible_set = set(only_visible_items)
        
        only_non_hidden_items = list(filter(lambda x: not( "_HIDDEN_" in x.key), only_visible_items))
        only_non_hidden_set = set(only_non_hidden_items)
        
        incorrect_non_hidden =  only_visible_set.difference(only_non_hidden_set)
        
        if incorrect_non_hidden:
            print("Items without hidden flag: ", end='')
            incorrect_names = map(lambda x: x.key, sorted(incorrect_non_hidden, key=lambda x: x.key))
            print(', '.join(incorrect_names))

        only_non_test_items = (
            filter(lambda x: True if x.related_hero is None else x.related_hero in only_real_hero_names,
                   only_non_hidden_items))

        return sorted(only_non_test_items, key=default_item_sorting_fn)

    def _process_items(self):
        # filter out any test and dummy heroes
        self.only_real_heroes: set[Unit] = set(
            filter(lambda x: x.is_hero and x.key != _dummy_hero and "_TEST" not in x.key, self.units))

        # prepare hero name filters
        only_real_hero_names = set(map(lambda x: x.key, self.only_real_heroes))

        self.visible_relics: list[Relic] = self._extract_visible_items(self.relics, only_real_hero_names)
        self.visible_consumables: list[Consumable] = self._extract_visible_items(self.consumables, only_real_hero_names)
        pass
