"""
download_pokemon_sprites.py  (forms.json-aware edition)
========================================================
Downloads sprites for every Pokémon form defined in your forms.json,
naming them exactly how your Discord bot expects:

    {base_id}.png            ← base / default form   (form_order == 1)
    {base_id}-1.png          ← first alternate form   (form_order == 2)
    {base_id}-2.png          ← second alternate form  (form_order == 3)
    … etc.

Custom / staff forms (identifiers ending in -staff or -custom) are skipped
automatically — they have custom sprites not sourced from PokeAPI.

Sprite resolution order (per form):
  1. PokeAPI HOME sprite  → high-quality, transparent-bg renders
  2. PokeAPI classic sprite  → classic battle sprites
  3. PokeAPI name-based lookup  → for forms whose pokemon_id doesn't map
     directly to a GitHub raw file (Ogerpon forms, Palafin-Hero, etc.)

Usage:
    python download_pokemon_sprites.py
    python download_pokemon_sprites.py -o ./sprites --forms forms.json
    python download_pokemon_sprites.py --classic-sprites   # use classic sprites
    python download_pokemon_sprites.py --no-skip           # re-download everything
    python download_pokemon_sprites.py --dry-run           # preview what would download

Requirements:
    pip install requests tqdm
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from tqdm import tqdm

# ── Config ─────────────────────────────────────────────────────────────────────

DEFAULT_OUTPUT  = "./pokemon_sprites"
DEFAULT_FORMS   = "forms.json"
DEFAULT_PFILE   = "pfile.json"

SPRITE_HOME_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/{pid}.png"
SPRITE_BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png"
API_BASE        = "https://pokeapi.co/api/v2"

DELAY           = 0.20      # seconds between requests
RETRY_LIMIT     = 4
RETRY_BACKOFF   = 2

# ── Identifiers that belong to custom / staff / bot-specific forms ──────────────
# These are skipped — they have no PokeAPI sprite.
CUSTOM_SUFFIXES    = ("-staff", "-custom")
CUSTOM_IDENTIFIERS = frozenset({
    "tatogod-arceus-staff", "alacatzam", "chichiri-oddish-staff",
    "dylee-gengar-custom", "sky-gengar-custom", "speedy-lugia-custom",
    "tsu-gardevoir-staff", "darling-gardevoir-custom", "krypt-rayquaza-custom",
    "gamer-piplup-staff", "silver-rotom-custom", "sunny-dialga-custom",
    "kanna-giratina", "giratinaorigin-kanna", "kt-zacian-staff",
    "kt-zacian.crowned-staff", "misfy-zorua-custom", "ru-keldeo-staff",
    "eaarl-zeraora-staff", "onehitmonchan", "eugene-missingmew-custom",
    "radio-rockruff-custom", "snowy-lycanroc-custom",
})

# Forms whose pokemon_id in forms.json is non-standard and need name lookup
NAME_LOOKUP_POKEMON_IDS = frozenset({
    8922,   # urshifu-rapid-strike  (custom local ID — real PokeAPI ID is 10116)
    11004,  # palafin-hero          (custom local ID — real PokeAPI ID is 10264)
    16010,  # toxtricity-low-key    (custom local ID — real PokeAPI ID is 10176)
    15000,  # urshifu-rapid-strike  (alternate custom ID)
})

# ── HTTP session ────────────────────────────────────────────────────────────────

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "PokemonDiscordBot-SpriteDownloader/1.0"})


def _get(url, binary=False, retries=RETRY_LIMIT):
    delay = RETRY_BACKOFF
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=15)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content if binary else r.json()
        except requests.RequestException:
            if attempt == retries - 1:
                return None
            time.sleep(delay)
            delay *= 2
    return None


def fetch_json(url):   return _get(url, binary=False)
def fetch_bytes(url):  return _get(url, binary=True)

# ── Sprite resolution ───────────────────────────────────────────────────────────

def png_valid(data):
    return data and data[:8] == b"\x89PNG\r\n\x1a\n"


def get_sprite_url(identifier, pokemon_id, use_home):
    """
    Returns the best available sprite URL for this form.

    Priority:
      1. GitHub raw HOME sprite   (by pokemon_id)
      2. GitHub raw classic sprite (by pokemon_id)
      3. PokeAPI JSON lookup       (by identifier name)
    """
    # Forms with known-bad local pokemon_ids skip straight to name lookup
    if pokemon_id not in NAME_LOOKUP_POKEMON_IDS:
        if use_home:
            url = SPRITE_HOME_URL.format(pid=pokemon_id)
            if png_valid(fetch_bytes(url)):
                return url
            time.sleep(DELAY)

        # Classic fallback
        url = SPRITE_BASE_URL.format(pid=pokemon_id)
        if png_valid(fetch_bytes(url)):
            return url
        time.sleep(DELAY)

    # Final fallback: look up by Pokémon name via PokeAPI
    poke_data = fetch_json(f"{API_BASE}/pokemon/{identifier}")
    if poke_data:
        sprites = poke_data.get("sprites", {})
        if use_home:
            home_url = (sprites.get("other") or {}).get("home", {}).get("front_default")
            if home_url:
                return home_url
        classic_url = sprites.get("front_default")
        if classic_url:
            return classic_url

    return None


def save_sprite(sprite_url, filepath):
    """Download sprite_url and save to filepath. Returns True on success."""
    if Path(filepath).exists():
        return True
    data = fetch_bytes(sprite_url)
    if png_valid(data):
        Path(filepath).write_bytes(data)
        return True
    return False

# ── Forms loading & filtering ───────────────────────────────────────────────────

def is_custom(form):
    ident = form.get("identifier", "")
    return (
        any(ident.endswith(s) for s in CUSTOM_SUFFIXES)
        or ident in CUSTOM_IDENTIFIERS
    )


def load_forms(forms_path):
    """
    Load forms.json → filter → deduplicate form_order collisions.

    Rules:
      - Keep only base_id 1–1025  (real national dex range)
      - Skip custom / staff forms
      - For duplicate (base_id, form_order) pairs, keep the entry with
        the lower form ID (real PokeAPI IDs < custom bot IDs)

    Returns a sorted list ready for download.
    """
    raw = json.loads(Path(forms_path).read_text())

    valid = [
        f for f in raw
        if f.get("base_id") and 1 <= f["base_id"] <= 1025 and not is_custom(f)
    ]

    # Deduplicate: for each (base_id, form_order), keep the entry with smallest id
    seen = {}
    for form in sorted(valid, key=lambda f: (f.get("id") or 99999)):
        key = (form["base_id"], form.get("form_order") or 1)
        if key not in seen:
            seen[key] = form

    return sorted(seen.values(), key=lambda f: (f["base_id"], f.get("form_order") or 1))


def build_download_plan(forms):
    """
    Convert filtered form list into download plan entries:
      { filename, identifier, pokemon_id, base_id, form_order }
    """
    plan = []
    for form in forms:
        base_id    = form["base_id"]
        form_order = form.get("form_order") or 1
        pokemon_id = form.get("pokemon_id") or base_id
        identifier = form.get("identifier", f"pokemon-{base_id}")

        filename = f"{base_id}.png" if form_order == 1 else f"{base_id}-{form_order - 1}.png"

        plan.append({
            "filename":   filename,
            "identifier": identifier,
            "pokemon_id": pokemon_id,
            "base_id":    base_id,
            "form_order": form_order,
        })
    return plan

# ── Main download loop ──────────────────────────────────────────────────────────

def download_all(output_dir, forms_path, use_home=True, skip_existing=True, dry_run=False):
    out = Path(output_dir)
    if not dry_run:
        out.mkdir(parents=True, exist_ok=True)

    print(f"\n\U0001f3ae  Pokemon Sprite Downloader  (forms.json edition)")
    print(f"   Output  : {out.resolve()}")
    print(f"   Forms   : {Path(forms_path).resolve()}")
    print(f"   Sprites : {'HOME (high-quality)' if use_home else 'classic battle'}")
    print(f"   Resume  : {skip_existing}")
    print(f"   Dry run : {dry_run}\n")

    forms = load_forms(forms_path)
    plan  = build_download_plan(forms)

    print(f"   Valid form entries : {len(forms)}")
    print(f"   Sprite files       : {len(plan)}\n")

    if dry_run:
        print("DRY RUN — files that would be downloaded:")
        for item in plan:
            exists = (out / item["filename"]).exists()
            status = "EXISTS   " if (exists and skip_existing) else "DOWNLOAD "
            print(f"  [{status}]  {item['filename']:<15}  {item['identifier']}"
                  f"  (pokemon_id={item['pokemon_id']})")
        return

    success = 0
    skipped = 0
    failed  = []
    log     = {}
    log_path = out / "sprite_download_log.json"

    if log_path.exists():
        try:
            log = json.loads(log_path.read_text())
        except Exception:
            pass

    pbar = tqdm(plan, desc="Sprites", unit="sprite", ncols=85)

    for item in pbar:
        filepath = out / item["filename"]
        pbar.set_postfix({"file": item["filename"], "ok": success, "fail": len(failed)})

        if skip_existing and filepath.exists():
            skipped += 1
            continue

        sprite_url = get_sprite_url(item["identifier"], item["pokemon_id"], use_home)
        time.sleep(DELAY)

        if not sprite_url:
            failed.append(item)
            tqdm.write(f"  ??? No sprite: {item['filename']}  ({item['identifier']})")
            continue

        ok = save_sprite(sprite_url, filepath)
        if ok:
            success += 1
            log[item["filename"]] = {
                "identifier": item["identifier"],
                "pokemon_id": item["pokemon_id"],
                "url": sprite_url,
            }
        else:
            failed.append(item)
            tqdm.write(f"  !! Download failed: {item['filename']}  ({item['identifier']})")

        time.sleep(DELAY)

        if success % 100 == 0 and success > 0:
            log_path.write_text(json.dumps(log, indent=2))

    log_path.write_text(json.dumps(log, indent=2))

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  OK       : {success} sprites downloaded")
    print(f"  Skipped  : {skipped} (already existed)")
    print(f"  Failed   : {len(failed)}")
    if failed:
        print(f"\n  Failed entries:")
        for f in failed[:25]:
            print(f"    {f['filename']}  ({f['identifier']})")
        if len(failed) > 25:
            print(f"    ... and {len(failed)-25} more — see {log_path}")
    print(f"\n  Log saved to: {log_path}")
    print(f"{'='*55}\n")

# ── CLI ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download Pokemon sprites from PokeAPI using forms.json as the source of truth."
    )
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT,
                        help=f"Folder to save sprites (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--forms", default=DEFAULT_FORMS,
                        help=f"Path to forms.json (default: {DEFAULT_FORMS})")
    parser.add_argument("--pfile", default=DEFAULT_PFILE,
                        help="Path to pfile.json (reserved for future use)")
    parser.add_argument("--classic-sprites", action="store_true",
                        help="Use classic battle sprites instead of HOME renders")
    parser.add_argument("--no-skip", action="store_true",
                        help="Re-download even if the file already exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be downloaded without downloading anything")

    args = parser.parse_args()

    if not Path(args.forms).exists():
        print(f"ERROR: forms.json not found at: {args.forms}")
        print(f"  Run update_pokemon_data.py first, or pass --forms <path>")
        sys.exit(1)

    try:
        download_all(
            output_dir    = args.output,
            forms_path    = args.forms,
            use_home      = not args.classic_sprites,
            skip_existing = not args.no_skip,
            dry_run       = args.dry_run,
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted — progress saved. Re-run to resume.")
        sys.exit(0)


if __name__ == "__main__":
    main()