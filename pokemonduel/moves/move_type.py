from ..enums import Ability, ElementType


class MoveType:
    """Move type determination."""

    def get_type(self, attacker, defender, battle):
        """
        Calculates the element type this move will be.
        """
        # Abilities are first because those are intrinsic to the poke and would "apply" to the move first
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.REFRIGERATE and self.type == ElementType.NORMAL:
            return ElementType.ICE
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.PIXILATE and self.type == ElementType.NORMAL:
            return ElementType.FAIRY
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.AERILATE and self.type == ElementType.NORMAL:
            return ElementType.FLYING
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.GALVANIZE and self.type == ElementType.NORMAL:
            return ElementType.ELECTRIC
        if attacker.ability() == Ability.NORMALIZE:
            return ElementType.NORMAL
        # pyrefly: ignore [missing-attribute]
        if attacker.ability() == Ability.LIQUID_VOICE and self.is_sound_based():
            return ElementType.WATER
        # pyrefly: ignore [missing-attribute]
        if self.type == ElementType.NORMAL and (attacker.ion_deluge or defender.ion_deluge or battle.plasma_fists):
            return ElementType.ELECTRIC
        if attacker.electrify:
            return ElementType.ELECTRIC
        # pyrefly: ignore [missing-attribute]
        if self.effect == 204:
            if battle.weather.get() == "hail":
                return ElementType.ICE
            if battle.weather.get() == "sandstorm":
                return ElementType.ROCK
            if battle.weather.get() in ("h-sun", "sun"):
                return ElementType.FIRE
            if battle.weather.get() in ("h-rain", "rain"):
                return ElementType.WATER
        if self.effect == 136:
            # Uses starting IVs as its own IVs should be used even if transformed.
            type_idx = attacker.starting_hpiv % 2
            type_idx += 2 * (attacker.starting_atkiv % 2)
            type_idx += 4 * (attacker.starting_defiv % 2)
            type_idx += 8 * (attacker.starting_speediv % 2)
            type_idx += 16 * (attacker.starting_spatkiv % 2)
            type_idx += 32 * (attacker.starting_spdefiv % 2)
            type_idx = (type_idx * 15) // 63
            type_options = {
                0:  ElementType.FIGHTING,
                1:  ElementType.FLYING,
                2:  ElementType.POISON,
                3:  ElementType.GROUND,
                4:  ElementType.ROCK,
                5:  ElementType.BUG,
                6:  ElementType.GHOST,
                7:  ElementType.STEEL,
                8:  ElementType.FIRE,
                9:  ElementType.WATER,
                10: ElementType.GRASS,
                11: ElementType.ELECTRIC,
                12: ElementType.PSYCHIC,
                13: ElementType.ICE,
                14: ElementType.DRAGON,
                15: ElementType.DARK,
            }
            return type_options[type_idx]
        if self.effect == 401:
            if len(attacker.type_ids) == 0:
                return ElementType.TYPELESS
            return attacker.type_ids[0]
        if self.effect == 269:
            if attacker.held_item in ("draco-plate", "dragon-memory"):
                return ElementType.DRAGON
            if attacker.held_item in ("dread-plate", "dark-memory"):
                return ElementType.DARK
            if attacker.held_item in ("earth-plate", "ground-memory"):
                return ElementType.GROUND
            if attacker.held_item in ("fist-plate", "fighting-memory"):
                return ElementType.FIGHTING
            if attacker.held_item in ("flame-plate", "burn-drive", "fire-memory"):
                return ElementType.FIRE
            if attacker.held_item in ("icicle-plate", "chill-drive", "ice-memory"):
                return ElementType.ICE
            if attacker.held_item in ("insect-plate", "bug-memory"):
                return ElementType.BUG
            if attacker.held_item in ("iron-plate", "steel-memory"):
                return ElementType.STEEL
            if attacker.held_item in ("meadow-plate", "grass-memory"):
                return ElementType.GRASS
            if attacker.held_item in ("mind-plate", "psychic-memory"):
                return ElementType.PSYCHIC
            if attacker.held_item in ("pixie-plate", "fairy-memory"):
                return ElementType.FAIRY
            if attacker.held_item in ("sky-plate", "flying-memory"):
                return ElementType.FLYING
            if attacker.held_item in ("splash-plate", "douse-drive", "water-memory"):
                return ElementType.WATER
            if attacker.held_item in ("spooky-plate", "ghost-memory"):
                return ElementType.GHOST
            if attacker.held_item in ("stone-plate", "rock-memory"):
                return ElementType.ROCK
            if attacker.held_item in ("toxic-plate", "poison-memory"):
                return ElementType.POISON
            if attacker.held_item in ("zap-plate", "shock-drive", "electric-memory"):
                return ElementType.ELECTRIC
        if self.effect == 223:
            hi = attacker.held_item.get()
            if hi in ("figy-berry", "tanga-berry", "cornn-berry", "enigma-berry"):
                return ElementType.BUG
            if hi in ("iapapa-berry", "colbur-berry", "spelon-berry", "rowap-berry", "maranga-berry"):
                return ElementType.DARK
            if hi in ("aguav-berry", "haban-berry", "nomel-berry", "jaboca-berry"):
                return ElementType.DRAGON
            if hi in ("pecha-berry", "wacan-berry", "wepear-berry", "belue-berry"):
                return ElementType.ELECTRIC
            if hi in ("roseli-berry", "kee-berry"):
                return ElementType.FAIRY
            if hi in ("leppa-berry", "chople-berry", "kelpsy-berry", "salac-berry"):
                return ElementType.FIGHTING
            if hi in ("cheri-berry", "occa-berry", "bluk-berry", "watmel-berry"):
                return ElementType.FIRE
            if hi in ("lum-berry", "coba-berry", "grepa-berry", "lansat-berry"):
                return ElementType.FLYING
            if hi in ("mago-berry", "kasib-berry", "rabuta-berry", "custap-berry"):
                return ElementType.GHOST
            if hi in ("rawst-berry", "rindo-berry", "pinap-berry", "liechi-berry"):
                return ElementType.GRASS
            if hi in ("persim-berry", "shuca-berry", "hondew-berry", "apicot-berry"):
                return ElementType.GROUND
            if hi in ("aspear-berry", "yache-berry", "pomeg-berry", "ganlon-berry"):
                return ElementType.ICE
            if hi in ("oran-berry", "kebia-berry", "qualot-berry", "petaya-berry"):
                return ElementType.POISON
            if hi in ("sitrus-berry", "payapa-berry", "tamato-berry", "starf-berry"):
                return ElementType.PSYCHIC
            if hi in ("wiki-berry", "charti-berry", "magost-berry", "micle-berry"):
                return ElementType.ROCK
            if hi in ("razz-berry", "babiri-berry", "pamtre-berry"):
                return ElementType.STEEL
            if hi in ("chesto-berry", "passho-berry", "nanab-berry", "durin-berry"):
                return ElementType.WATER
            if hi == "chilan-berry":
                return ElementType.NORMAL
        if self.effect == 433 and attacker._name == "Morpeko-hangry":
            return ElementType.DARK
        if self.effect == 441 and attacker.grounded(battle):
            if battle.terrain.item == "electric":
                return ElementType.ELECTRIC
            if battle.terrain.item == "grass":
                return ElementType.GRASS
            if battle.terrain.item == "misty":
                return ElementType.FAIRY
            if battle.terrain.item == "psychic":
                return ElementType.PSYCHIC
        # pyrefly: ignore [missing-attribute]
        if self.id == 873:
            if attacker._name == "Tauros-paldea":
                return ElementType.FIGHTING
            if attacker._name == "Tauros-aqua-paldea":
                return ElementType.WATER
            if attacker._name == "Tauros-blaze-paldea":
                return ElementType.FIRE

        # pyrefly: ignore [missing-attribute]
        return self.type
