import random
from ..enums import Ability, DamageClass, ElementType


class DuelPokemonMechanics:
    """Pokemon transformation, forms, type effectiveness, weight, and abilities."""

    def transform(self, otherpoke):
        """Transforms this poke into otherpoke."""
        self.choice_move = None
        self._name = otherpoke._name
        # pyrefly: ignore [missing-attribute]
        if self._nickname != "None":
            self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
        else:
            self.name = self._name.replace("-", " ")
        self.attack = otherpoke.attack
        self.defense = otherpoke.defense
        self.spatk = otherpoke.spatk
        self.spdef = otherpoke.spdef
        self.speed = otherpoke.speed
        self.hpiv = otherpoke.hpiv
        self.atkiv = otherpoke.atkiv
        self.defiv = otherpoke.defiv
        self.spatkiv = otherpoke.spatkiv
        self.spdefiv = otherpoke.spdefiv
        self.speedev = otherpoke.speedev
        self.hpev = otherpoke.hpev
        self.atkev = otherpoke.atkev
        self.defev = otherpoke.defev
        self.spatkev = otherpoke.spatkev
        self.spdefev = otherpoke.spdefev
        self.speedev = otherpoke.speedev
        self.moves = [move.copy() for move in otherpoke.moves]
        for m in self.moves:
            m.pp = 5
        self.ability_id = otherpoke.ability_id
        self.type_ids = otherpoke.type_ids.copy()
        self.attack_stage = otherpoke.attack_stage
        self.defense_stage = otherpoke.defense_stage
        self.spatk_stage = otherpoke.spatk_stage
        self.spdef_stage = otherpoke.spdef_stage
        self.speed_stage = otherpoke.speed_stage
        self.accuracy_stage = otherpoke.accuracy_stage
        self.evasion_stage = otherpoke.evasion_stage
    
    def form(self, form: str):
        """
        Changes this poke's form to the provided form.
        
        This changes its name and base stats, and may affect moves, abilities, and items.
        Returns True if the poke successfully reformed.
        """
        # pyrefly: ignore [missing-attribute]
        if form not in self.base_stats:
            return False
        self._name = form
        # pyrefly: ignore [missing-attribute]
        if self._nickname != "None":
            self.name = f"{self._nickname} ({self._name.replace('-', ' ')})"
        else:
            self.name = self._name.replace("-", " ")
        # pyrefly: ignore [missing-attribute]
        self.attack = self.base_stats[self._name][1]
        # pyrefly: ignore [missing-attribute]
        self.defense = self.base_stats[self._name][2]
        # pyrefly: ignore [missing-attribute]
        self.spatk = self.base_stats[self._name][3]
        # pyrefly: ignore [missing-attribute]
        self.spdef = self.base_stats[self._name][4]
        # pyrefly: ignore [missing-attribute]
        self.speed = self.base_stats[self._name][5]
        self.attack_split = None
        self.spatk_split = None
        self.defense_split = None
        self.spdef_split = None
        self.autotomize = 0
        return True
    
    def effectiveness(self, attacker_type: ElementType, battle, *, attacker=None, move=None):
        """Calculates a float representing the effectiveness of `attacker_type` damage on this poke."""
        if attacker_type == ElementType.TYPELESS:
            return 1
        effectiveness = 1
        for defender_type in self.type_ids:
            if defender_type == ElementType.TYPELESS:
                continue
            if move is not None and move.effect == 380 and defender_type == ElementType.WATER:
                effectiveness *= 2
                continue
            # pyrefly: ignore [missing-attribute]
            if move is not None and move.effect == 373 and defender_type == ElementType.FLYING and not self.grounded(battle, attacker=attacker, move=move):
                return 1 # Ignores secondary types if defender is flying type and not grounded
            # pyrefly: ignore [missing-attribute]
            if self.roost and defender_type == ElementType.FLYING:
                continue
            # pyrefly: ignore [missing-attribute]
            if self.foresight and attacker_type in (ElementType.FIGHTING, ElementType.NORMAL) and defender_type == ElementType.GHOST:
                continue
            # pyrefly: ignore [missing-attribute]
            if self.miracle_eye and attacker_type == ElementType.PSYCHIC and defender_type == ElementType.DARK:
                continue
            if (
                attacker_type in (ElementType.FIGHTING, ElementType.NORMAL)
                and defender_type == ElementType.GHOST
                and attacker is not None
                and attacker.ability() in [Ability.SCRAPPY, Ability.MINDS_EYE]
            ):
                continue
            # pyrefly: ignore [missing-attribute]
            if attacker_type == ElementType.GROUND and defender_type == ElementType.FLYING and self.grounded(battle, attacker=attacker, move=move):
                continue
            e = battle.type_effectiveness[(attacker_type, defender_type)] / 100
            if defender_type == ElementType.FLYING and e > 1 and move is not None and battle.weather.get() == "h-wind":
                e = 1
            if battle.inverse_battle:
                if e < 1:
                    e = 2
                elif e > 1:
                    e = 0.5
            effectiveness *= e
        # pyrefly: ignore [missing-attribute]
        if attacker_type == ElementType.FIRE and self.tar_shot:
            effectiveness *= 2
        # pyrefly: ignore [missing-attribute]
        if effectiveness >= 1 and self.hp == self.starting_hp and self.ability(attacker=attacker, move=move) == Ability.TERA_SHELL:
            effectiveness = 0.5
        return effectiveness
    
    def weight(self, *, attacker=None, move=None):
        """
        Returns this pokemon's current weight.
        
        Dynamically modifies the weight based on the ability of this pokemon.
        """
        cur_ability = self.ability(attacker=attacker, move=move)
        # pyrefly: ignore [missing-attribute]
        cur_weight = self.starting_weight
        if cur_ability == Ability.HEAVY_METAL:
            cur_weight *= 2
        if cur_ability == Ability.LIGHT_METAL:
            cur_weight //= 2
            cur_weight = max(1, cur_weight)
        cur_weight -= self.autotomize * 1000
        cur_weight = max(1, cur_weight)
        return cur_weight
        
    
    def ability(self, *, attacker=None, move=None):
        """
        Returns this pokemon's current ability.
        
        Returns None in cases where the ability is blocked or nullified.
        """
        # Currently there are two categories of ability ignores, and both only apply when a move is used.
        # Since this could change, the method signature is flexable. However, without both present, it
        # should not consider the existing options.
        if move is None or attacker is None or attacker is self:
            return self.ability_id
        if not self.ability_ignorable():
            return self.ability_id
        if move.effect in (411, 460):
            return None
        if attacker.ability_id in (Ability.MOLD_BREAKER, Ability.TURBOBLAZE, Ability.TERAVOLT, Ability.NEUTRALIZING_GAS):
            return None
        if attacker.ability_id == Ability.MYCELIUM_MIGHT and move.damage_class == DamageClass.STATUS:
            return None
        return self.ability_id
    
    def ability_changeable(self):
        """Returns True if this pokemon's current ability can be changed."""
        return self.ability_id not in (
            Ability.MULTITYPE, Ability.STANCE_CHANGE, Ability.SCHOOLING, Ability.COMATOSE,
            Ability.SHIELDS_DOWN, Ability.DISGUISE, Ability.RKS_SYSTEM, Ability.BATTLE_BOND,
            Ability.POWER_CONSTRUCT, Ability.ICE_FACE, Ability.GULP_MISSILE, Ability.ZERO_TO_HERO
        )
    
    def ability_giveable(self):
        """Returns True if this pokemon's current ability can be given to another pokemon."""
        return self.ability_id not in (
            Ability.TRACE, Ability.FORECAST, Ability.FLOWER_GIFT, Ability.ZEN_MODE, Ability.ILLUSION,
            Ability.IMPOSTER, Ability.POWER_OF_ALCHEMY, Ability.RECEIVER, Ability.DISGUISE, Ability.STANCE_CHANGE,
            Ability.POWER_CONSTRUCT, Ability.ICE_FACE, Ability.HUNGER_SWITCH, Ability.GULP_MISSILE, Ability.ZERO_TO_HERO
        )
    
    def ability_ignorable(self):
        """Returns True if this pokemon's current ability can be ignored."""
        return self.ability_id in (
            Ability.AROMA_VEIL, Ability.BATTLE_ARMOR, Ability.BIG_PECKS, Ability.BULLETPROOF, Ability.CLEAR_BODY,
            Ability.CONTRARY, Ability.DAMP, Ability.DAZZLING, Ability.DISGUISE, Ability.DRY_SKIN, Ability.FILTER,
            Ability.FLASH_FIRE, Ability.FLOWER_GIFT, Ability.FLOWER_VEIL, Ability.FLUFFY, Ability.FRIEND_GUARD,
            Ability.FUR_COAT, Ability.HEATPROOF, Ability.HEAVY_METAL, Ability.HYPER_CUTTER, Ability.ICE_FACE,
            Ability.ICE_SCALES, Ability.IMMUNITY, Ability.INNER_FOCUS, Ability.INSOMNIA, Ability.KEEN_EYE,
            Ability.LEAF_GUARD, Ability.LEVITATE, Ability.LIGHT_METAL, Ability.LIGHTNING_ROD, Ability.LIMBER,
            Ability.MAGIC_BOUNCE, Ability.MAGMA_ARMOR, Ability.MARVEL_SCALE, Ability.MIRROR_ARMOR, Ability.MOTOR_DRIVE,
            Ability.MULTISCALE, Ability.OBLIVIOUS, Ability.OVERCOAT, Ability.OWN_TEMPO, Ability.PASTEL_VEIL,
            Ability.PUNK_ROCK, Ability.QUEENLY_MAJESTY, Ability.SAND_VEIL, Ability.SAP_SIPPER, Ability.SHELL_ARMOR,
            Ability.SHIELD_DUST, Ability.SIMPLE, Ability.SNOW_CLOAK, Ability.SOLID_ROCK, Ability.SOUNDPROOF,
            Ability.STICKY_HOLD, Ability.STORM_DRAIN, Ability.STURDY, Ability.SUCTION_CUPS, Ability.SWEET_VEIL,
            Ability.TANGLED_FEET, Ability.TELEPATHY, Ability.THICK_FAT, Ability.UNAWARE, Ability.VITAL_SPIRIT,
            Ability.VOLT_ABSORB, Ability.WATER_ABSORB, Ability.WATER_BUBBLE, Ability.WATER_VEIL, Ability.WHITE_SMOKE,
            Ability.WONDER_GUARD, Ability.WONDER_SKIN, Ability.ARMOR_TAIL, Ability.EARTH_EATER, Ability.GOOD_AS_GOLD,
            Ability.PURIFYING_SALT, Ability.WELL_BAKED_BODY
        )
    
    def get_assist_move(self):
        """
        Returns a Move that can be used with assist, or None if none exists.
        
        This selects a random move from the pool of moves from pokes in the user's party that are eligable.
        """
        moves = []
        # pyrefly: ignore [missing-attribute]
        for idx, poke in enumerate(self.owner.party):
            # pyrefly: ignore [missing-attribute]
            if idx == self.owner.last_idx:
                continue
            for move in poke.moves:
                if move.selectable_by_assist():
                    moves.append(move)
        if not moves:
            return None
        return random.choice(moves)
