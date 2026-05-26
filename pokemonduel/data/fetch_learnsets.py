import json
import urllib.request
import ssl
from pathlib import Path

def main():
    url = "https://play.pokemonshowdown.com/data/learnsets.json"
    print(f"Fetching from {url}...")
    
    # Bypass SSL verification to avoid potential local environment issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching from api: {e}")
        return

    print("Processing learnsets...")
    compiled = {}
    for pokemon, details in data.items():
        if isinstance(details, dict) and "learnset" in details:
            moves = list(details["learnset"].keys())
            # Store lowercase, kebab-case move names
            compiled[pokemon] = [m.lower().strip() for m in moves]

    output_path = Path(__file__).parent / "learnsets.json"
    print(f"Saving compiled learnsets to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(compiled, f, indent=2)
    print(f"Done! Saved {len(compiled)} Pokémon learnsets.")

if __name__ == "__main__":
    main()
