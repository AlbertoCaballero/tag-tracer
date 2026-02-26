from typing import Any, Dict, List

def string_to_list(s):
    """
    Parses a string that represents a list, e.g., "[item1, item2]".
    """
    s = s.strip("[]")
    return [item.strip() for item in s.split(",") if item.strip()]


def format_expected_tags(tags: Dict[str, Any] = {}) -> str:
    """
    Takes the expected tags and forms a readable output string.
    """
    formatted_lines = []
    for tag_key, tag_value in tags.items():
        if isinstance(tag_value, dict) and "value" in tag_value:
            # If it's an ExpectedTag-like dictionary with a 'value'
            formatted_lines.append(f"  - {tag_key}: {tag_value['value']}")
        else:
            # Otherwise, just print the value directly
            formatted_lines.append(f"  - {tag_key}: {tag_value}")
    return "\n".join(formatted_lines)

def print_expected_tags(tags: Dict[str, Any] = {}):
    """
    Takes the expected tags and forms a readable output
    """
    format = ""
    for tag in tags:
        print(f"{'\t' * 1}{tag}: {tags[tag]}")
        format.join(f"\n{'\t' * 1}{tag}: {tags[tag]}")
    return format
