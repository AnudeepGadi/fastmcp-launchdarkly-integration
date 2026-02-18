from typing import Literal


def convert_temperature(temperature: float, unit: Literal["C", "F"]) -> float:
    if unit == "C":
        return ((9 / 5) * temperature) + 32
    elif unit == "F":
        return (5 / 9) * (temperature - 32)
    else:
        raise ValueError(f"Unknown unit: {unit}")
