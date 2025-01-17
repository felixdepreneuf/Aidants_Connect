from enum import IntEnum, auto, unique


@unique
class HabilitationFormStep(IntEnum):
    ISSUER = auto()
    ORGANISATION = auto()
    PERSONNEL = auto()
    SUMMARY = auto()
