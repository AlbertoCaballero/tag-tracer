from typing import List


def string_to_list(s) -> List[str]:
    """
    Parses a string that represents a list, e.g., "[item1, item2]".
    """
    s = s.strip("[]")
    return [item.strip() for item in s.split(",") if item.strip()]