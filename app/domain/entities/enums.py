from enum import Enum


class PrivacyVisibility(Enum):
    EVERYONE    = "EVERYONE"
    CONTACTS    = "CONTACTS"
    NOBODY      = "NOBODY"


class TwoFAMethod(Enum):
    TOTP        = "TOTP"
    SMS         = "SMS"
    NONE        = "NONE"


class Platform(Enum):
    IOS         = "IOS"
    ANDROID     = "ANDROID"
    WEB         = "WEB"
    DESKTOP     = "DESKTOP"


class ChatType(Enum):
    PRIVATE     = "PRIVATE"
    GROUP       = "GROUP"
    SECRET      = "SECRET"
    CHANNEL     = "CHANNEL"


class ChatRole(Enum):
    OWNER       = "OWNER"
    ADMIN       = "ADMIN"
    MEMBER      = "MEMBER"
    SUBSCRIBER  = "SUBSCRIBER"