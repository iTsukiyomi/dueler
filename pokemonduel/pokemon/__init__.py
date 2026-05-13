from .pokemon_init import DuelPokemonInit
from .pokemon_send_out import DuelPokemonSendOut
from .pokemon_turn import DuelPokemonTurn
from .pokemon_damage import DuelPokemonDamage
from .pokemon_stats import DuelPokemonStats
from .pokemon_mechanics import DuelPokemonMechanics

from ..moves import Move
from ..enums import ElementType
from ..data_gen.query import find, find_one


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
    """Creates a new DuelPokemon object using the raw data provided."""
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
    nature = raw_data["nature"]
    gender = raw_data["gender"]

    nature = await find_one(ctx, "natures", {"identifier": nature.lower()})
    dec_stat_id = nature["decreased_stat_id"]
    inc_stat_id = nature["increased_stat_id"]
    dec_stat = await find_one(ctx, "stat_types", {"id": dec_stat_id})
    inc_stat = await find_one(ctx, "stat_types", {"id": inc_stat_id})
    dec_stat = dec_stat["identifier"].capitalize().replace("-", " ")
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
        nature_stat_deltas[dec_stat] = 0.9
        nature_stat_deltas[inc_stat] = 1.1
        disliked_flavor = flavor_map[dec_stat]

    #Deform pokes that are formed into battle forms that they should not start off in
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
    #TODO: Meloetta, Shaymin

    form_info = await find_one(ctx, "forms", {"identifier": pn.lower()})

    # Handle duplicate form entries - if pokemon_id doesn't have valid ptypes, find another
    pokemon_id = form_info["pokemon_id"]
    type_ids_entry = await find_one(ctx, "ptypes", {"id": pokemon_id})
    if type_ids_entry is None:
        # Search for another form entry with same identifier that has valid ptypes
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

    #List of type ids
    type_ids = type_ids_entry["types"]
    
    #6 element list of stat values (int)
    stats = (await find_one(ctx, "pokemon_stats", {"pokemon_id": form_info["pokemon_id"]}))["stats"]
    pokemonHp = stats[0]
    
    #Store the base stats for all forms of this poke
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
        f_stats = (await find_one(ctx, "pokemon_stats", {"pokemon_id": f_info["pokemon_id"]}))["stats"]
        base_stats[f_name] = f_stats

    #Builds a list of the possible ability ids for this poke, `ab_index` is the currently selected ability from this list
    ab_ids = []
    for record in await find(ctx, "poke_abilities", {"pokemon_id": form_info["pokemon_id"]}):
        ab_ids.append(record["ability_id"])

    try:
        ab_id = ab_ids[ab_index]
    #Should never happen, but better safe than sorry
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
        pid = (await find_one(ctx, "forms", {"identifier": name}))["pokemon_id"]
    else:
        pid = form_info["pokemon_id"]

    #True if any possible future evo exists
    can_still_evolve = bool(await find_one(ctx, "pfile", {"evolves_from_species_id": pid}))
    #Unreleased pokemon that is treated like a form in the bot, monkeypatch fix.
    if pn == "Floette-eternal":
        can_still_evolve = False

    #This stat can (/has to) be calculated ahead of time, as it does not change between forms.
    #If transform copied HP, I would probably take up drinking...
    pokemonHp = round((((2 * pokemonHp + hpiv + (hpev / 4)) * plevel) / 100) + plevel + 10)
    
    hitem = await find_one(ctx, "items", {"identifier": hitem})

    if pn == "Shedinja":
        pokemonHp = 1
    
    weight = (await find_one(ctx, "forms", {"identifier": pn.lower()}))["weight"]
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