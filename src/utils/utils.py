from typing import Any, Dict, List

"""
tag_tracer string_to_list is a function that takes a string of [a, b, c] and returns List[str]
"""
def string_to_list(s):
    s = s.strip("[]")
    return [item.strip() for item in s.split(",")]

"""
Takes the expected tags and forms a readable output
"""
def format_expected_tags(tags: Dict[str, Any] = {}):
    format = ""
    for tag in tags:
        print(f"{'\t' * 1}{tag}: {tags[tag]}")
        format.join(f"\n{'\t' * 1}{tag}: {tags[tag]}")
    return format
