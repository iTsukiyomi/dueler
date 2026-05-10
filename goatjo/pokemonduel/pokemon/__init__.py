from .pokemon_init import DuelPokemonInit
from .pokemon_send_out import DuelPokemonSendOut
from .pokemon_turn import DuelPokemonTurn
from .pokemon_damage import DuelPokemonDamage
from .pokemon_stats import DuelPokemonStats
from .pokemon_mechanics import DuelPokemonMechanics


class DuelPokemon(
    DuelPokemonInit,
    DuelPokemonSendOut,
    DuelPokemonTurn,
    DuelPokemonDamage,
    DuelPokemonStats,
    DuelPokemonMechanics
):
    pass


from ..misc import ExpiringEffect, NonVolatileEffect, Metronome
from ..misc import LockedMove
from ..enums import Ability, ElementType
from ..data_gen.query import find_one
import random


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
    base_stats = find_one("BaseStats", name=pn)
    poke = DuelPokemon(
        pokemon_id=id,
        name=pn,
        nickname=nick,
        base_stats=base_stats,
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
        nature_stat_deltas=raw_data["nature_stat_deltas"],
        item=hitem,
        shiny=shiny,
        gender=raw_data["gender"],
        happiness=happiness,
        can_still_evolve=raw_data["can_still_evolve"],
        moves=moves,
        ability_id=Ability[raw_data["ability"].upper().replace(" ", "_")],
        mega_ability_id=Ability[raw_data["mega_ability"].upper().replace(" ", "_")] if raw_data["mega_ability"] != "None" else None,
    )

    poke.starting_weight = poke.base_stats[pn][6]

    poke.confusion = ExpiringEffect("confusion", 0)
    poke.foresight = ExpiringEffect("foresight", 0)
    poke.miracle_eye = ExpiringEffect("miracle_eye", 0)
    poke.telekinesis = ExpiringEffect("telekinesis", 0)
    poke.fairy_lock = ExpiringEffect("fairy_lock", 0)

    poke.protect = False
    poke.wide_guard = False
    poke.crafty_shield = False
    poke.king_shield = False
    poke.spiky_shield = False
    poke.mat_block = False
    poke.baneful_bunker = False
    poke.quick_guard = False
    poke.obstruct = False
    poke.silk_trap = False
    poke.burning_bulwark = False
    poke.protection_used = False
    poke.protection_chance = 1
    poke.endure = False
    poke.last_protect_counter = 0

    poke.laser_focus = ExpiringEffect("laser_focus", 0)
    poke.powdered = False
    poke.beak_blast = False
    poke.grudge = False

    poke.echoed_voice_power = 40
    poke.echoed_voice_used = False

    poke.choiced_move = None

    poke.stockpile = 0

    poke.charge = ExpiringEffect("charge", 0)
    poke.magnet_rise = ExpiringEffect("magnet_rise", 0)
    poke.embargo = ExpiringEffect("embargo", 0)
    poke.heal_block = ExpiringEffect("heal_block", 0)

    poke.tailwind = ExpiringEffect("tailwind", 0)

    poke.flinched = False
    poke.has_moved = False
    poke.truant_turn = 0
    poke.recharge_turn = False

    poke.locked_move = None
    poke.dive = False
    poke.dig = False
    poke.fly = False
    poke.shadow_force = False
    poke.bide = ExpiringEffect("bide", 0)

    poke.destiny_bond = False
    poke.destiny_bond_cooldown = ExpiringEffect("destiny_bond_cooldown", 0)

    poke.crit_stage = 0

    poke.mind_reader = ExpiringEffect("mind_reader", 0)
    poke.lock_on = False
    poke.accuracy_stage = 0
    poke.evasion_stage = 0

    poke.curse = False
    poke.aqua_ring = False
    poke.ingrain = False

    poke.leech_seed = False
    poke.perish_song = ExpiringEffect("perish_song", 0)

    poke.tar_shot = False

    poke.attack_stage = 0
    poke.defense_stage = 0
    poke.spatk_stage = 0
    poke.spdef_stage = 0
    poke.speed_stage = 0

    poke.illusion__name = None
    poke.illusion_name = None
    poke.ever_sent_out = False

    poke.power_trick = False

    poke.autotomize = 0

    poke.power_shift = False

    poke.substitute = 0
    poke.roost = False
    poke.terastallized = False

    poke.active_turns = 0
    poke.swapped_in = True

    poke.stat_increased = False
    poke.stat_decreased = False

    poke.is_dynamaxed = 0

    poke.last_move_failed = False
    poke.last_move_damage = None

    poke.ability_boosted = False

    poke.ice_repaired = False

    poke.smack_down = False

    poke.truant = False

    poke.nv = NonVolatileEffect(poke)
    poke.metronome = Metronome(poke)
    poke.baton_pass = None

    poke.lolly = []
    poke.encore = ExpiringEffect("encore", 0)

    poke.self_switch = False
    poke.switch_in_turns = ExpiringEffect("switch_in_turns", 0)

    poke.cud_chew = ExpiringEffect("cud_chew", 0)

    poke.disable = ExpiringEffect("disable", 0)

    poke.uproar = ExpiringEffect("uproar", 0)

    poke.infatuated = None

    poke.bind = LockedMove("bind")

    poke.rage = False
    poke.stored_power = 0

    poke.used_z_move = False

    poke.booster_energy = False

    poke.syrup_bomb = ExpiringEffect("syrup_bomb", 0)

    poke.last_berry = None

    poke.can_tera = True
    poke.can_dynamax = True

    poke.do_deserialize(raw_data)

    if radiant:
        poke.held_item = "none"
        poke.ability_id = Ability.RADIANT

    poke.shiny = shiny

    poke.type_ids = list(poke.starting_type_ids)

    return poke