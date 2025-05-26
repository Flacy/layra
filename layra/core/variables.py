import re
from typing import Match

PATTERN = re.compile(r"\{\{(\w+)\}\}")


def substitute(content: str, *, variables: dict[str, str]) -> str:
    def replace_var(match: Match):
        return variables.get(match.group(1), match.group(0))

    return PATTERN.sub(replace_var, content)
