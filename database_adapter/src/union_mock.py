def isMember(shortcode: str) -> bool:
    return True

def has_labpass(shortcode : str) -> bool:
    return True


def getShortcodesToCIDAndName(shortcodes) -> list:
    return [("", "", s) for s in shortcodes]


def isMemberList(shortcodes: list[str]) -> bool:
    return shortcodes
