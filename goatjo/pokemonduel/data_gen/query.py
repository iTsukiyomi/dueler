import json
from pathlib import Path


async def find(ctx, db, filter):
    """Fetch all matching rows from a data file."""
    # Get the directory where your data files are located
    # ctx parameter is kept for compatibility, but we'll use a fixed path
    data_dir = Path(__file__).parent.parent / "data"
    path = data_dir / f"{db}.json"

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for item in data:
        success = True
        for key, value in filter.items():
            if isinstance(value, dict):
                if "$nin" in value:
                    if item[key] in value["$nin"]:
                        success = False
                        break
            else:
                if item[key] != value:
                    success = False
                    break
        if success:
            results.append(item)
    return results


async def find_one(ctx, db, filter):
    """Fetch the first matching row from a data file."""
    results = await find(ctx, db, filter)
    if results:
        return results[0]
    return None