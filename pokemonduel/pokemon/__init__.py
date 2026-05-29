from .pokemon_init import DuelPokemonInit
from .pokemon_send_out import DuelPokemonSendOut
from .pokemon_turn import DuelPokemonTurn
from .pokemon_damage import DuelPokemonDamage
from .pokemon_stats import DuelPokemonStats
from .pokemon_mechanics import DuelPokemonMechanics

from ..moves import Move
from ..enums import ElementType
from ..data_gen.query import find, find_one


# pyrefly: ignore [inconsistent-inheritance]
class DuelPokemon(
    DuelPokemonInit,
    DuelPokemonSendOut,
    DuelPokemonTurn,
    DuelPokemonDamage,
    DuelPokemonStats,
    DuelPokemonMechanics
):
    pass


async def create(ctx, raw_data: dict):
    """Create a new DuelPokemon instance from a raw data dictionary."""
    pn = raw_data["pokname"]
    nick = raw_data["poknick"]
    hpiv = min(31, raw_data["hpiv"])
    atkiv = min(31, raw_data["atkiv"])
    defiv = min(31, raw_data["defiv"])
    spatkiv = min(31, raw_data["spatkiv"])
    spdefiv = min(31, raw_data["spdefiv"])
    speediv = min(31, raw_data["speediv"])
    hpev = raw_data["hpev"]
    atkev = raw_data["atkev"]
    defev = raw_data["defev"]
    spaev = raw_data["spatkev"]
    spdev = raw_data["spdefev"]
    speedev = raw_data["speedev"]
    plevel = raw_data["pokelevel"]
    shiny = raw_data["shiny"]
    radiant = raw_data["radiant"]
    skin = raw_data["skin"]
    id = raw_data["id"]
    hitem = raw_data["hitem"]
    happiness = raw_data["happiness"]
    moves = raw_data["moves"]
    ab_index = raw_data["ability_index"]
    nature_name = raw_data["nature"]
    gender = raw_data["gender"]

    nature = await find_one(ctx, "natures", {"identifier": nature_name.lower()})
    # pyrefly: ignore [unsupported-operation]
    dec_stat_id = nature["decreased_stat_id"]
    # pyrefly: ignore [unsupported-operation]
    inc_stat_id = nature["increased_stat_id"]
    dec_stat = await find_one(ctx, "stat_types", {"id": dec_stat_id})
    inc_stat = await find_one(ctx, "stat_types", {"id": inc_stat_id})
    # pyrefly: ignore [unsupported-operation]
    dec_stat = dec_stat["identifier"].capitalize().replace("-", " ")
    # pyrefly: ignore [unsupported-operation]
    inc_stat = inc_stat["identifier"].capitalize().replace("-", " ")
    nature_stat_deltas = {"Attack": 1, "Defense": 1, "Special attack": 1, "Special defense": 1, "Speed": 1}
    flavor_map = {
        "Attack": "spicy",
        "Defense": "sour",
        "Speed": "sweet",
        "Special attack": "dry",
        "Special defense": "bitter",
    }
    disliked_flavor = ""
    if dec_stat != inc_stat:
        # pyrefly: ignore [bad-typed-dict-key]
        nature_stat_deltas[dec_stat] = 0.9
        # pyrefly: ignore [bad-typed-dict-key]
        nature_stat_deltas[inc_stat] = 1.1
        disliked_flavor = flavor_map[dec_stat]

    # Reset battle-only forms to their base species on initialization.
    if pn == "Mimikyu-busted":
        pn = "Mimikyu"
    if pn in ("Cramorant-gorging", "Cramorant-gulping"):
        pn = "Cramorant"
    if pn == "Eiscue-noice":
        pn = "Eiscue"
    if pn == "Darmanitan-zen":
        pn = "Darmanitan"
    if pn == "Darmanitan-zen-galar":
        pn = "Darmanitan-galar"
    if pn == "Aegislash-blade":
        pn = "Aegislash"
    if pn in ("Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet"):
        pn = "Minior"
    if pn == "Wishiwashi" and plevel >= 20:
        pn = "Wishiwashi-school"
    if pn == "Wishiwashi-school" and plevel < 20:
        pn = "Wishiwashi"
    if pn == "Greninja-ash":
        pn = "Greninja"
    if pn == "Zygarde-complete":
        pn = "Zygarde"
    if pn == "Morpeko-hangry":
        pn = "Morpeko"
    if pn == "Cherrim-sunshine":
        pn = "Cherrim"
    if pn in ("Castform-snowy", "Castform-rainy", "Castform-sunny"):
        pn = "Castform"
    if pn in (
        "Arceus-dragon",
        "Arceus-dark",
        "Arceus-ground",
        "Arceus-fighting",
        "Arceus-fire",
        "Arceus-ice",
        "Arceus-bug",
        "Arceus-steel",
        "Arceus-grass",
        "Arceus-psychic",
        "Arceus-fairy",
        "Arceus-flying",
        "Arceus-water",
        "Arceus-ghost",
        "Arceus-rock",
        "Arceus-poison",
        "Arceus-electric",
    ):
        pn = "Arceus"
    if pn in (
        "Silvally-psychic",
        "Silvally-fairy",
        "Silvally-flying",
        "Silvally-water",
        "Silvally-ghost",
        "Silvally-rock",
        "Silvally-poison",
        "Silvally-electric",
        "Silvally-dragon",
        "Silvally-dark",
        "Silvally-ground",
        "Silvally-fighting",
        "Silvally-fire",
        "Silvally-ice",
        "Silvally-bug",
        "Silvally-steel",
        "Silvally-grass",
    ):
        pn = "Silvally"
    if pn == "Palafin-hero":
        pn = "Palafin"
    if pn.endswith("-mega-x") or pn.endswith("-mega-y"):
        pn = pn[:-7]
    if pn.endswith("-mega"):
        pn = pn[:-5]

    form_info = await find_one(ctx, "forms", {"identifier": pn.lower()})

    # Scan all forms for a matching identifier if primary lookup misses.
    if form_info is None:
        all_forms = await find(ctx, "forms", {"identifier": pn.lower()})
        if all_forms:
            form_info = all_forms[0]

    # Normalise separators and run token substring matching for non-canonical format fallbacks.
    if form_info is None:
        all_forms = await find(ctx, "forms", {})
        norm_pn = pn.lower().replace("-", "").replace(" ", "").replace("_", "")
        for f in all_forms:
            iden = f.get("identifier", "")
            if iden.replace("-", "").replace(" ", "").replace("_", "") == norm_pn:
                form_info = f
                break
        if form_info is None:
            best_score = 0
            for f in all_forms:
                iden = f.get("identifier", "").lower()
                if not iden:
                    continue
                tokens = iden.split("-")
                if not tokens or not all(t in norm_pn for t in tokens):
                    continue
                score = sum(len(t) for t in tokens)
                if score > best_score:
                    form_info = f
                    best_score = score

    if form_info is None:
        raise ValueError(
            f"Unknown Pokémon form {pn!r} (original name: {raw_data['pokname']!r}). "
            "This species is missing from forms.json – skipping team slot."
        )

    pokemon_id = form_info["pokemon_id"]
    type_ids_entry = await find_one(ctx, "ptypes", {"id": pokemon_id})
    if type_ids_entry is None:
        all_forms = await find(ctx, "forms", {"identifier": pn.lower()})
        for alt_form in all_forms:
            alt_pid = alt_form.get("pokemon_id")
            if alt_pid and alt_pid != pokemon_id:
                alt_entry = await find_one(ctx, "ptypes", {"id": alt_pid})
                if alt_entry:
                    form_info = alt_form
                    pokemon_id = alt_pid
                    type_ids_entry = alt_entry
                    break

    # pyrefly: ignore [unsupported-operation]
    type_ids = type_ids_entry["types"]

    stats_entry = await find_one(ctx, "pokemon_stats", {"pokemon_id": form_info["pokemon_id"]})
    if stats_entry is None:
        # Fall back to base form ID if the alternate form has no unique stat entry.
        base_iden = form_info.get("identifier", "").split("-")[0]
        base_form = await find_one(ctx, "forms", {"identifier": base_iden})
        if base_form is not None:
            stats_entry = await find_one(
                ctx, "pokemon_stats", {"pokemon_id": base_form["pokemon_id"]}
            )
    if stats_entry is None:
        raise ValueError(
            f"Missing pokemon_stats for form {pn!r} (pokemon_id={form_info['pokemon_id']})."
        )
    stats = stats_entry["stats"]
    pokemonHp = stats[0]

    base_stats = {}
    base_stats[pn] = stats
    extra_forms = []
    if pn == "Mimikyu":
        extra_forms = ["Mimikyu-busted"]
    if pn == "Cramorant":
        extra_forms = ["Cramorant-gorging", "Cramorant-gulping"]
    if pn == "Eiscue":
        extra_forms = ["Eiscue-noice"]
    if pn == "Darmanitan":
        extra_forms = ["Darmanitan-zen"]
    if pn == "Darmanitan-galar":
        extra_forms = ["Darmanitan-zen-galar"]
    if pn == "Aegislash":
        extra_forms = ["Aegislash-blade"]
    if pn == "Minior":
        extra_forms = ["Minior-red", "Minior-orange", "Minior-yellow", "Minior-green", "Minior-blue", "Minior-indigo", "Minior-violet"]
    if pn == "Wishiwashi":
        extra_forms = ["Wishiwashi-school"]
    if pn == "Wishiwashi-school":
        extra_forms = ["Wishiwashi"]
    if pn == "Greninja":
        extra_forms = ["Greninja-ash"]
    if pn == "Zygarde":
        extra_forms = ["Zygarde-complete"]
    if pn == "Zygarde-10":
        extra_forms = ["Zygarde-complete"]
    if pn == "Morpeko":
        extra_forms = ["Morpeko-hangry"]
    if pn == "Cherrim":
        extra_forms = ["Cherrim-sunshine"]
    if pn == "Castform":
        extra_forms = ["Castform-snowy", "Castform-rainy", "Castform-sunny"]
    if pn == "Arceus":
        extra_forms = [
            "Arceus-dragon",
            "Arceus-dark",
            "Arceus-ground",
            "Arceus-fighting",
            "Arceus-fire",
            "Arceus-ice",
            "Arceus-bug",
            "Arceus-steel",
            "Arceus-grass",
            "Arceus-psychic",
            "Arceus-fairy",
            "Arceus-flying",
            "Arceus-water",
            "Arceus-ghost",
            "Arceus-rock",
            "Arceus-poison",
            "Arceus-electric",
        ]
    if pn == "Silvally":
        extra_forms = [
            "Silvally-psychic",
            "Silvally-fairy",
            "Silvally-flying",
            "Silvally-water",
            "Silvally-ghost",
            "Silvally-rock",
            "Silvally-poison",
            "Silvally-electric",
            "Silvally-dragon",
            "Silvally-dark",
            "Silvally-ground",
            "Silvally-fighting",
            "Silvally-fire",
            "Silvally-ice",
            "Silvally-bug",
            "Silvally-steel",
            "Silvally-grass",
        ]
    if pn == "Palafin":
        extra_forms = ["Palafin-hero"]
    mega_form = None
    mega_ability_id = None
    mega_type_ids = None
    if pn != "Rayquaza":
        if hitem == "mega-stone":
            mega_form = pn + "-mega"
        elif hitem == "mega-stone-x":
            mega_form = pn + "-mega-x"
        elif hitem == "mega-stone-y":
            mega_form = pn + "-mega-y"
    else:
        if "dragon-ascent" in moves:
            mega_form = pn + "-mega"
    if mega_form is not None:
        mega_form_info = await find_one(ctx, "forms", {"identifier": mega_form.lower()})
        if mega_form_info is not None:
            mega_ability = await find_one(ctx, "poke_abilities", {"pokemon_id": mega_form_info["pokemon_id"]})
            if mega_ability is None:
                raise ValueError("mega form missing ability in `poke_abilities`")
            mega_ability_id = mega_ability["ability_id"]
            mega_types = (await find_one(ctx, "ptypes", {"id": mega_form_info["pokemon_id"]}))
            if mega_types is None:
                raise ValueError("mega form missing types in `ptypes`")
            mega_type_ids = mega_types["types"]
            extra_forms.append(mega_form)

    for f_name in extra_forms:
        f_info = await find_one(ctx, "forms", {"identifier": f_name.lower()})
        if f_info is None:
            # Reuse base stats for extra forms not present in database to avoid lookup crashes.
            base_stats[f_name] = stats
            continue
        f_stats_entry = await find_one(
            ctx, "pokemon_stats", {"pokemon_id": f_info["pokemon_id"]}
        )
        if f_stats_entry is None:
            base_stats[f_name] = stats
        else:
            base_stats[f_name] = f_stats_entry["stats"]

    ab_ids = []
    for record in await find(ctx, "poke_abilities", {"pokemon_id": form_info["pokemon_id"]}):
        ab_ids.append(record["ability_id"])

    try:
        ab_id = ab_ids[ab_index]
    except IndexError:
        ab_id = ab_ids[0]

    if any(
        pn.endswith(suffix)
        for suffix in [
            "-bug","-summer","-marine","-elegant","-poison","-average","-altered","-winter","-trash","-incarnate",
            "-baile","-rainy","-steel","-star","-ash","-diamond","-pop-star","-fan","-school","-therian","-pau",
            "-river","-poke-ball","-kabuki","-electric","-heat","-unbound","-chill","-archipelago","-zen","-normal",
            "-mega-y","-resolute","-blade","-speed","-indigo","-dusk","-sky","-west","-sun","-dandy","-solo","-high-plains",
            "-la-reine","-50","-unova-cap","-burn","-mega-x","-monsoon","-primal","-red-striped","-blue-striped",
            "-white-striped","-ground","-super","-yellow","-polar","-cosplay","-ultra","-heart","-snowy","-sensu",
            "-eternal","-douse","-defense","-sunshine","-psychic","-modern","-natural","-tundra","-flying","-pharaoh",
            "-libre","-sunny","-autumn","-10","-orange","-standard","-land","-partner","-dragon","-plant","-pirouette",
            "-male","-hoenn-cap","-violet","-spring","-fighting","-sandstorm","-original-cap","-neutral","-fire",
            "-fairy","-attack","-black","-shock","-shield","-shadow","-grass","-continental","-overcast","-disguised",
            "-exclamation","-origin","-garden","-blue","-matron","-red-meteor","-small","-rock-star","-belle",
            "-alola-cap","-green","-active","-red","-mow","-icy-snow","-debutante","-east","-midday","-jungle","-frost",
            "-midnight","-rock","-fancy","-busted","-ordinary","-water","-phd","-ice","-spiky-eared","-savanna","-original",
            "-ghost","-meadow","-dawn","-question","-pom-pom","-female","-kalos-cap","-confined","-sinnoh-cap","-aria",
            "-dark","-ocean","-wash","-white","-mega","-sandy","-complete","-large","-crowned","-ice-rider","-shadow-rider",
            "-zen-galar","-rapid-strike","-noice","-hangry",
        ]
    ):
        name = pn.lower().split("-")[0]
        base_form = await find_one(ctx, "forms", {"identifier": name})
        # Fall back to current form ID if base name split fails to match forms.json.
        if base_form is None:
            pid = form_info["pokemon_id"]
        else:
            pid = base_form["pokemon_id"]
    else:
        pid = form_info["pokemon_id"]

    can_still_evolve = bool(await find_one(ctx, "pfile", {"evolves_from_species_id": pid}))
    # Monkeypatch evolves-from lookup for Floette-Eternal.
    if pn == "Floette-eternal":
        can_still_evolve = False

    # Calculate HP beforehand as it remains constant across form changes.
    pokemonHp = round((((2 * pokemonHp + hpiv + (hpev / 4)) * plevel) / 100) + plevel + 10)

    hitem = await find_one(ctx, "items", {"identifier": hitem})

    if pn == "Shedinja":
        pokemonHp = 1

    weight_form = await find_one(ctx, "forms", {"identifier": pn.lower()})
    if weight_form is None:
        weight_form = form_info
    weight = weight_form.get("weight") if weight_form is not None else None
    if weight is None:
        weight = 20

    object_moves = []
    for move in moves:
        type_override = None
        if move.startswith("hidden-power-"):
            element = move.split("-")[2]
            move = "hidden-power"
            type_override = ElementType[element.upper()]
        move = await find_one(ctx, "moves", {"identifier": move})
        if move is None:
            move = await find_one(ctx, "moves", {"identifier": "tackle"})
        else:
            if type_override is not None:
                move["type_id"] = type_override
        # pyrefly: ignore [bad-unpacking]
        object_moves.append(Move(**move))
    p = DuelPokemon(
        pokemon_id=pid,
        name=pn,
        nickname=nick,
        base_stats=base_stats,
        hp=pokemonHp,
        hpiv=hpiv,
        atkiv=atkiv,
        defiv=defiv,
        spatkiv=spatkiv,
        spdefiv=spdefiv,
        speediv=speediv,
        hpev=hpev,
        atkev=atkev,
        defev=defev,
        spatkev=spaev,
        spdefev=spdev,
        speedev=speedev,
        level=plevel,
        nature_stat_deltas=nature_stat_deltas,
        nature=nature_name,
        shiny=shiny,
        radiant=radiant,
        skin=skin,
        type_ids=type_ids,
        mega_type_ids=mega_type_ids,
        id=id,
        held_item=hitem,
        happiness=happiness,
        moves=object_moves,
        ability_id=ab_id,
        mega_ability_id=mega_ability_id,
        weight=weight,
        gender=gender,
        can_still_evolve=can_still_evolve,
        disliked_flavor=disliked_flavor,
    )

    return p
