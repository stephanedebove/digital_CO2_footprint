from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from loguru import logger


class Assumptions:
    """All configurable factors used in calculations, dynamically loaded from assumptions.yaml."""

    def __init__(self, assumptions_path: Path):
        self._decimals_map: Dict[Tuple[str, Optional[str]], int] = {}
        self.load_from_yaml(assumptions_path)

    def __getitem__(self, key: str):
        """Allow dict-like access (assumptions["variable"])."""
        return getattr(self, key)

    def load_from_yaml(self, assumptions_path: Path):
        """Load all variables from assumptions.yaml and set them as attributes."""
        with assumptions_path.open("r", encoding="utf-8") as f:
            raw_text = f.read()
        yaml_data = yaml.safe_load(raw_text)

        # Compute decimal places per variable/subkey based on raw YAML to preserve trailing zeros
        self._decimals_map = _compute_decimals_map_from_yaml(raw_text)

        for key, value in yaml_data.items():
            # Ensure all values are converted to float if possible
            if isinstance(value, dict):
                setattr(self, key, {k: float(v) for k, v in value.items()})
            else:
                setattr(self, key, float(value))

    def get_decimals(self, variable: str, subkey: Optional[str] = None) -> int:
        """Return the number of decimal digits specified in YAML for a variable.

        Args:
            variable: Top-level variable name.
            subkey: Optional second-level key for nested mappings.

        Returns:
            The number of decimal digits to display/record. Defaults to 2 if not found.
        """
        return self._decimals_map.get(
            (variable, subkey), self._decimals_map.get((variable, None), 2)
        )


def _compute_decimals_map_from_yaml(
    raw_text: str,
) -> Dict[Tuple[str, Optional[str]], int]:
    """Parse YAML text to capture decimal places for each numeric default, preserving trailing zeros.

    This lightweight parser walks lines, tracks indentation and parent keys, and records decimal
    places for numeric scalars using their literal text. Supports simple key: value and nested
    mappings used in assumptions.yaml.

    Args:
        raw_text: YAML content as a string.

    Returns:
        Mapping from (variable, subkey) to decimal count. For top-level scalars, subkey is None.
    """
    import re

    decimals_map: Dict[Tuple[str, Optional[str]], int] = {}
    stack: List[Tuple[int, str]] = []  # (indent, key)

    lines = raw_text.splitlines()
    for line in lines:
        # Strip comments and trailing spaces
        no_comment = line.split("#", 1)[0].rstrip()
        if not no_comment.strip():
            continue
        indent = len(no_comment) - len(no_comment.lstrip(" "))
        content = no_comment.lstrip(" ")
        if ":" not in content:
            continue
        key_part, value_part = content.split(":", 1)
        key = key_part.strip()
        value = value_part.strip()

        # Maintain stack for nesting
        while stack and stack[-1][0] >= indent:
            stack.pop()

        if value == "":
            # Start of a mapping
            stack.append((indent, key))
            continue

        # Numeric literal detection
        m = re.match(r"^-?\d+(?:\.(\d+))?$", value)
        if m:
            decimals = len(m.group(1)) if m.group(1) else 0
            # Build path
            parents = [k for _, k in stack]
            if parents:
                top = parents[0]
                subkey = key
                decimals_map[(top, subkey)] = decimals
            else:
                decimals_map[(key, None)] = decimals

    return decimals_map


def load_assumptions() -> Assumptions:
    """Load assumptions from YAML, returning an Assumptions instance."""
    assumptions_path = Path(__file__).parent / "assumptions.yaml"
    if not assumptions_path.exists():
        raise FileNotFoundError(f"Assumptions file not found at {assumptions_path}")
    return Assumptions(assumptions_path)
