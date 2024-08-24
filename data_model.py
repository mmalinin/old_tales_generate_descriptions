import xml.etree.ElementTree as ElementTree
from enum import Enum


class BaseItem:
    def __init__(self, element: ElementTree.Element):
        elem_name = element.find(".//visual//name")
        self.name = elem_name.text if elem_name is not None else None

        elem_descr = element.find(".//visual//desc")
        self.descr = elem_descr.text if elem_descr is not None else None

        self.key = element.attrib["key"]
        pass


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

        elem_quality = element.find(".//quality")
        self.quality = int(elem_quality.text) if elem_quality is not None else None

        elem_related_hero = element.find(".//related_hero")
        self.related_hero = elem_related_hero.text if elem_related_hero is not None else None

        item_type_str = self.get_item_type_str()
        self.quality_str = f"{item_type_str}_{self.quality}" if item_type_str is not None else None

        elem_source = element.find(".//source")
        self.source = int(elem_source.text) if elem_source is not None else None

        elem_flag = element.find(".//flags")
        self.flag = elem_flag is not None
        
        is_hidden = False
        # TODO: use better way to find single tag
        for i in element:
            if i.tag == "hidden_flag":
                is_hidden = True
                break
        
        self.hidden = is_hidden or self.source is None

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
        if self.source is not None:
            return f"_{self.get_item_source_name()}_"
        else:
            return ""


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

        elem_cost = element.find(".//cost")
        self.cost = int(elem_cost.text) if elem_cost is not None else None

        elem_upgrade = element.find(".//upgrade")
        self.upgrade = elem_upgrade.text if elem_upgrade is not None else None

        elem_type = element.find(".//type")
        self.card_type = int(elem_type.text) if elem_type is not None else None

        elem_intention = element.find(".//visual//intention")
        self.is_mob = elem_intention is not None

    def get_item_type_str(self):
        return "CARD_TYPE"

    def get_card_type_name(self):
        if self.card_type is not None:
            type_u = Card.CardType(self.card_type)
            return f"{self.get_item_type_str()}_{type_u.name}"


class Unit(BaseItem):
    def __init__(self, element: ElementTree.Element):
        super().__init__(element)

        elem_hp = element.find(".//hp")
        self.hp = int(elem_hp.text) if elem_hp is not None else None

        elem_attack = element.find(".//attack")
        self.attack = int(elem_attack.text) if elem_attack is not None else None

        elem_armor = element.find(".//armor")
        self.armor = int(elem_armor.text) if elem_armor is not None else None

        elem_nickname = element.find(".//visual//nickname")
        self.nickname = elem_nickname.text if elem_nickname is not None else None

        elem_hero = element.find(".//type//hero")
        self.is_hero = elem_hero is not None


class Config:
    def __init__(self, root: ElementTree.Element):
        self.relics: list[Relic] = []
        self.consumables: list[Consumable] = []
        self.cards: list[Card] = []
        self.units: list[Unit] = []

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
