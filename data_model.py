import xml.etree.ElementTree as ElementTree
from enum import Enum


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
        self.quality = safe_get_int(element, ".//quality")
        self.related_hero = safe_get_text(element, ".//related_hero")
        self.quality_str = f"{self.get_item_type_str()}_{self.quality}" if self.get_item_type_str() else None
        self.source = safe_get_int(element, ".//source")
        self.flag: bool = element.find(".//flags") is not None
        self.hidden = any(child.tag == "hidden_flag" for child in element) or self.source is None

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
        self.is_mob = element.find(".//visual//intention") is not None

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


class Config:
    def __init__(self, root: ElementTree.Element):
        self.relics: list[Relic] = []
        self.consumables: list[Consumable] = []
        self.cards: list[Card] = []
        self.units: list[Unit] = []
        self._load_items(root)

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
