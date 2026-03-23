import re

ALLOWED_SIZES = ["2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "6XL"]
ALLOWED_SIZE_SET = set(ALLOWED_SIZES)

_ONLY_NUMBERS = re.compile(r"^\d+$")
_RANGE_ONLY = re.compile(r"^\d+\s*-\s*\d+$")
_DASHED_SUFFIX = re.compile(r"[-_/]\s*\d+[a-z]*$")


def normalize_size(raw: str | None) -> str | None:
    if raw is None:
        return None

    value = raw.strip().lower()
    if not value:
        return None

    if "cm" in value or "kg" in value:
        return None
    if re.search(r"\d+\s*x\s*\d+", value):
        return None
    if _ONLY_NUMBERS.fullmatch(value):
        return None
    if _RANGE_ONLY.fullmatch(value):
        return None

    value = value.replace("lång", "").replace("lang", "").replace("kort", "")
    value = _DASHED_SUFFIX.sub("", value)
    value = re.sub(r"\s+", " ", value).strip()

    if value.startswith("xxs") or value.startswith("2xs"):
        return "2XS"
    if value.startswith("xs"):
        return "XS"
    if value in {"s", "small", "s/m"} or value.startswith("s-"):
        return "S"
    if value in {"m", "medium"} or value.startswith("m-"):
        return "M"
    if value in {"l", "large"} or value.startswith("l-"):
        return "L"
    if value.startswith("xl") or value == "xliten":
        return "XL"
    if value.startswith("2xl") or value.startswith("xxl"):
        return "2XL"
    if value.startswith("3xl"):
        return "3XL"
    if value.startswith("4xl"):
        return "4XL"
    if value.startswith("5xl") or value.startswith("xxxxxl"):
        return "5XL"
    if value.startswith("6xl") or value.startswith("xxxxxxl"):
        return "6XL"

    return None
