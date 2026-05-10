import random
from ..enums import Ability, DamageClass, ElementType


class DuelPokemonDamage:
    """Pokemon damage and healing logic."""

    def faint(self, battle, *, move=None, attacker=None, source: str=""):
        """
        Sets a pokemon's HP to zero and cleans it up.
        
        If a pokemon takes damage equal to its HP, use damage instead.
        This method ignores focus sash and sturdy, forcing the pokemon to faint.
        Returns a formatted message.
        """
        msg = ""
        self.hp = 0
        if source:
            source = f" from {source}"
        msg += f"{self.name} fainted{source}!\n"
        if move is not None and attacker is not None and self.destiny_bond and self.owner.has_alive_pokemon():
            msg += attacker.faint(battle, source=f"{self.name}'s destiny bond")
        if move is not None and attacker is not None and attacker._name == "Greninja" and attacker.ability() == Ability.BATTLE_BOND:
            if attacker.form("Greninja-ash"):
                msg += f"{attacker.name}'s bond with its trainer has strengthened it!\n"
        if move is not None and self.grudge:
            move.pp = 0
            msg += f"{move.pretty_name}'s pp was depleted!\n"
        if attacker is not None and attacker.ability() in (Ability.CHILLING_NEIGH, Ability.AS_ONE_ICE):
            msg += attacker.append_attack(1, attacker=attacker, source="its chilling neigh")
        if attacker is not None and attacker.ability() in (Ability.GRIM_NEIGH, Ability.AS_ONE_SHADOW):
            msg += attacker.append_spatk(1, attacker=attacker, source="its grim neigh")
        for poke in (battle.trainer1.current_pokemon, battle.trainer2.current_pokemon):
            if poke is not None and poke is not self and poke.ability() == Ability.SOUL_HEART:
                msg += poke.append_spatk(
                    1,
                    attacker=poke,
                    source="its soul heart"
                )
        self.owner.retaliate.set_turns(2)
        self.owner.num_fainted += 1
        msg += self.remove(battle, fainted=True)
        return msg
    
    def damage(self, damage, battle, *, move=None, move_type=None, attacker=None, critical=False, drain_heal_ratio=None, source: str=""):
        """
        Applies a certain amount of damage to this pokemon.
        
        Returns a formatted message.
        """
        msgadd, _ = self._damage(damage, battle, move=move, move_type=move_type, attacker=attacker, critical=critical, drain_heal_ratio=drain_heal_ratio, source=source)
        return msgadd
    
    def _damage(self, damage, battle, *, move=None, move_type=None, attacker=None, critical=False, drain_heal_ratio=None, source: str=""):
        """
        Applies a certain amount of damage to this pokemon.
        
        Returns a formatted message and the amount of damage actually dealt.
        """
        msg = ""
        # Don't go through with an attack if the poke is already dead.
        # If this is a bad idea for *some* reason, make sure to add an `attacker is self` check to INNARDS_OUT.
        if self.hp <= 0:
            return "", 0
        previous_hp = self.hp
        damage = max(1, damage)
        
        # Magic guard
        if self.ability(attacker=attacker, move=move) == Ability.MAGIC_GUARD and move is None and attacker is not self:
            return f"{self.name}'s magic guard protected it from damage!\n", 0
        
        # Substitute
        if (
            self.substitute
            and move is not None and move.is_affected_by_substitute() and not move.is_sound_based()
            and (attacker is None or attacker.ability() != Ability.INFILTRATOR)
        ):
            # is_affected_by_substitute should be a superset of is_sound_based, but it's better to check both to be sure.
            msg += f"{self.name}'s substitute took {damage} damage{source}!\n"
            new_hp = max(0, self.substitute - damage)
            true_damage = self.substitute - new_hp
            self.substitute = new_hp
            if self.substitute == 0:
                msg += f"{self.name}'s substitute broke!\n"
            return msg, true_damage
        
        # Damage blocking forms / abilities
        if move is not None:
            if self.ability(attacker=attacker, move=move) == Ability.DISGUISE and self._name == "Mimikyu":
                if self.form("Mimikyu-busted"):
                    msg += f"{self.name}'s disguise was busted!\n"
                    msg += self.damage(self.starting_hp // 8, battle, source="losing its disguise")
                    return msg, 0
            if self.ability(attacker=attacker, move=move) == Ability.ICE_FACE and self._name == "Eiscue" and move.damage_class == DamageClass.PHYSICAL:
                if self.form("Eiscue-noice"):
                    msg += f"{self.name}'s ice face was busted!\n"
                    return msg, 0
        
        # OHKO protection
        self.dmg_this_turn = True
        if damage >= self.hp and move is not None:
            if self.endure:
                msg += f"{self.name} endured the hit!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.ability(attacker=attacker, move=move) == Ability.STURDY:
                msg += f"{self.name} endured the hit with its Sturdy!\n"
                damage = self.hp - 1
            elif self.hp == self.starting_hp and self.held_item == "focus-sash":
                msg += f"{self.name} held on using its focus sash!\n"
                damage = self.hp - 1
                self.held_item.use()
            elif self.held_item == "focus-band" and not random.randrange(10):
                msg += f"{self.name} held on using its focus band!\n"
                damage = self.hp - 1
        
        # Apply the damage
        dropped_below_half = self.hp > self.starting_hp / 2
        dropped_below_quarter = self.hp > self.starting_hp / 4
        
        new_hp = max(0, self.hp - damage)
        true_damage = self.hp - new_hp
        self.hp = new_hp
        
        dropped_below_half = dropped_below_half and self.hp <= self.starting_hp / 2
        dropped_below_quarter = dropped_below_quarter and self.hp <= self.starting_hp / 4
        if source:
            source = f" from {source}"
        msg += f"{self.name} took {damage} damage{source}!\n"
        self.num_hits += 1
        
        # Drain
        if drain_heal_ratio is not None and attacker is not None:
            heal = true_damage * drain_heal_ratio
            if attacker.held_item == "big-root":
                heal = heal * 1.3
            heal = int(heal)
            if self.ability() == Ability.LIQUID_OOZE:
                msg += attacker.damage(heal, battle, source=f"{self.name}'s liquid ooze")
            else:
                if not attacker.heal_block.active():
                    msg += attacker.heal(heal, source=source)
        
        if self.hp == 0:
            msg += self.faint(battle, move=move, attacker=attacker)
            if (
                self.ability() == Ability.AFTERMATH
                and attacker is not None
                and attacker is not self
                and attacker.ability() != Ability.DAMP
                and move is not None
                and move.makes_contact(attacker)
            ):
                msg += attacker.damage(attacker.starting_hp // 4, battle, source=f"{self.name}'s aftermath")
            if attacker is not None and attacker.ability() == Ability.MOXIE:
                msg += attacker.append_attack(1, attacker=attacker, source="its moxie")
            if attacker is not None and attacker.ability() == Ability.BEAST_BOOST:
                stats = (
                    (attacker.get_raw_attack(), attacker.append_attack),
                    (attacker.get_raw_defense(), attacker.append_defense),
                    (attacker.get_raw_spatk(), attacker.append_spatk),
                    (attacker.get_raw_spdef(), attacker.append_spdef),
                    (attacker.get_raw_speed(), attacker.append_speed),
                )
                append_func = sorted(stats, reverse=True, key=lambda s: s[0])[0][1]
                msg += append_func(1, attacker=attacker, source="its beast boost")
            if attacker is not None and self.ability() == Ability.INNARDS_OUT:
                msg += attacker.damage(previous_hp, battle, attacker=self, source=f"{self.name}'s innards out")
        elif move is not None and move_type is not None:
            if move_type == ElementType.FIRE and self.nv.freeze():
                self.nv.reset()
                msg += f"{self.name} thawed out!\n"
            if move.effect in (458, 500) and self.nv.freeze():
                self.nv.reset()
                msg += f"{self.name} thawed out!\n"
            if self.ability() == Ability.COLOR_CHANGE and move_type not in self.type_ids:
                self.type_ids = [move_type]
                t = ElementType(move_type).name.lower()
                msg += f"{self.name} changed its color, transforming into a {t} type!\n"
            if self.ability() == Ability.ANGER_POINT and critical:
                msg += self.append_attack(6, attacker=self, source="its anger point")
            if self.ability() == Ability.WEAK_ARMOR and move.damage_class == DamageClass.PHYSICAL and attacker is not self:
                msg += self.append_defense(-1, attacker=self, source="its weak armor")
                msg += self.append_speed(2, attacker=self, source="its weak armor")
            if self.ability() == Ability.JUSTIFIED and move_type == ElementType.DARK:
                msg += self.append_attack(1, attacker=self, source="justified")
            if self.ability() == Ability.RATTLED and move_type in (ElementType.BUG, ElementType.DARK, ElementType.GHOST):
                msg += self.append_speed(1, attacker=self, source="its rattled")
            if self.ability() == Ability.STAMINA:
                msg += self.append_defense(1, attacker=self, source="its stamina")
            if self.ability() == Ability.WATER_COMPACTION and move_type == ElementType.WATER:
                msg += self.append_defense(2, attacker=self, source="its water compaction")
            if self.ability() == Ability.BERSERK and dropped_below_half:
                msg += self.append_spatk(1, attacker=self, source="its berserk")
            if self.ability() == Ability.ANGER_SHELL and dropped_below_half:
                msg += self.append_attack(1, attacker=self, source="its anger shell")
                msg += self.append_spatk(1, attacker=self, source="its anger shell")
                msg += self.append_speed(1, attacker=self, source="its anger shell")
                msg += self.append_defense(-1, attacker=self, source="its anger shell")
                msg += self.append_spdef(-1, attacker=self, source="its anger shell")
            if self.ability() == Ability.STEAM_ENGINE and move_type in (ElementType.FIRE, ElementType.WATER):
                msg += self.append_speed(6, attacker=self, source="its steam engine")
            if self.ability() == Ability.THERMAL_EXCHANGE and move_type == ElementType.FIRE:
                msg += self.append_attack(1, attacker=self, source="its thermal exchange")
            if self.ability() == Ability.WIND_RIDER and move.is_wind():
                msg += self.append_attack(1, attacker=self, source="its wind rider")
            if self.ability() == Ability.COTTON_DOWN and attacker is not None:
                msg += attacker.append_speed(-1, attacker=self, source=f"{self.name}'s cotton down")
            if self.ability() == Ability.SAND_SPIT:
                msg += battle.weather.set("sandstorm", self)
            if self.ability() == Ability.SEED_SOWER and battle.terrain.item is None:
                msg += battle.terrain.set("grassy", self)
            if self.ability() == Ability.ELECTROMORPHOSIS:
                self.charge.set_turns(2)
                msg += f"{self.name} became charged by its electromorphosis!\n"
            if self.ability() == Ability.WIND_POWER and move.is_wind():
                self.charge.set_turns(2)
                msg += f"{self.name} became charged by its wind power!\n"
            if self.ability() == Ability.TOXIC_DEBRIS and move.damage_class == DamageClass.PHYSICAL:
                if attacker is not None and attacker is not self and attacker.owner.toxic_spikes < 2:
                    attacker.owner.toxic_spikes += 1
                    msg += f"Toxic spikes were scattered around the feet of {attacker.owner.name}'s team because of {self.name}'s toxic debris!\n"
            if self.illusion_name is not None:
                self._name = self.illusion__name
                self.name = self.illusion_name
                self.illusion__name = None
                self.illusion_name = None
                msg += f"{self.name}'s illusion broke!\n"
            if self.held_item == "air-balloon":
                self.held_item.remove()
                msg += f"{self.name}'s air balloon popped!\n"
        
        if move is not None:
            self.last_move_damage = (max(1, damage), move.damage_class)
            if self.bide is not None:
                self.bide += damage
            if self.rage:
                msg += self.append_attack(1, attacker=self, source="its rage")
            if attacker is not None:
                if (
                    self.ability() == Ability.CURSED_BODY
                    and not attacker.disable.active()
                    and move in attacker.moves
                    and random.randint(1, 100) <= 30
                ):
                    if attacker.ability() == Ability.AROMA_VEIL:
                        msg += f"{attacker.name}'s aroma veil protects its move from being disabled!\n"
                    else:
                        attacker.disable.set(move, 4)
                        msg += f"{attacker.name}'s {move.pretty_name} was disabled by {self.name}'s cursed body!\n"
                if attacker.ability() == Ability.MAGICIAN and not attacker.held_item.has_item() and self.held_item.can_remove():
                    self.held_item.transfer(attacker.held_item)
                    msg += f"{attacker.name} stole {attacker.held_item.name} using its magician!\n"
                if attacker.ability() == Ability.TOXIC_CHAIN and random.randint(1, 100) <= 30:
                    msg += self.nv.apply_status("b-poison", battle, attacker=attacker, source=f"{attacker.name}'s toxic chain")
                if attacker.held_item == "shell-bell":
                    # Shell bell does not trigger when a move is buffed by sheer force.
                    if attacker.ability() != Ability.SHEER_FORCE or move.effect_chance is None:
                        msg += attacker.heal(damage // 8, source="its shell bell")
            msg += self.held_item.activate_on_damage(damage, attacker, move, battle)
        
        # Retreat
        if dropped_below_half and sum(x.hp > 0 for x in self.owner.party) > 1:
            if self.ability() == Ability.WIMP_OUT:
                msg += f"{self.name} wimped out and retreated!\n"
                msg += self.remove(battle)
            elif self.ability() == Ability.EMERGENCY_EXIT:
                msg += f"{self.name} used the emergency exit and retreated!\n"
                msg += self.remove(battle)
        
        # Gulp Missile
        if attacker is not None and self._name in ("Cramorant-gulping", "Cramorant-gorging") and self.owner.has_alive_pokemon():
            prey = "pikachu" if self._name == "Cramorant-gorging" else "arrokuda"
            if self.form("Cramorant"):
                msg += attacker.damage(attacker.starting_hp // 4, battle, source=f"{self.name} spitting out its {prey}")
                if prey == "arrokuda":
                    msg += attacker.append_defense(-1, attacker=self, source=f"{self.name} spitting out its {prey}")
                elif prey == "pikachu":
                    msg += attacker.nv.apply_status("paralysis", battle, attacker=self, source=f"{self.name} spitting out its {prey}")
        
        # Berries
        if self.held_item.should_eat_berry_damage(attacker):
            msg += self.held_item.eat_berry(attacker=attacker, move=move)
        
        # Contact
        if move is not None and attacker is not None and move.makes_contact(attacker):
            # Affects ATTACKER
            if attacker.held_item != "protective-pads":
                if self.beak_blast:
                    msg += attacker.nv.apply_status("burn", battle, attacker=attacker, source=f"{self.name}'s charging beak blast")
                if self.ability() == Ability.STATIC:
                    if random.randint(1, 100) <= 30:
                        msg += attacker.nv.apply_status("paralysis", battle, attacker=attacker, source=f"{self.name}'s static")
                if self.ability() == Ability.POISON_POINT:
                    if random.randint(1, 100) <= 30:
                        msg += attacker.nv.apply_status("poison", battle, attacker=attacker, source=f"{self.name}'s poison point")
                if self.ability() == Ability.FLAME_BODY:
                    if random.randint(1, 100) <= 30:
                        msg += attacker.nv.apply_status("burn", battle, attacker=attacker, source=f"{self.name}'s flame body")
                if self.ability() == Ability.ROUGH_SKIN and self.owner.has_alive_pokemon():
                    msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{self.name}'s rough skin")
                if self.ability() == Ability.IRON_BARBS and self.owner.has_alive_pokemon():
                    msg += attacker.damage(attacker.starting_hp // 8, battle, source=f"{self.name}'s iron barbs")
                if self.ability() == Ability.EFFECT_SPORE:
                    if (
                        attacker.ability() != Ability.OVERCOAT
                        and ElementType.GRASS not in attacker.type_ids
                        and attacker.held_item != "safety-glasses"
                        and random.randint(1, 100) <= 30
                    ):
                        status = random.choice(["paralysis", "poison", "sleep"])
                        msg += attacker.nv.apply_status(status, battle, attacker=attacker)
                if self.ability() == Ability.CUTE_CHARM and random.randint(1, 100) <= 30:
                    msg += attacker.infatuate(self, source=f"{self.name}'s cute charm")
                if self.ability() == Ability.MUMMY and attacker.ability() != Ability.MUMMY and attacker.ability_changeable():
                    attacker.ability_id = Ability.MUMMY
                    msg += f"{attacker.name} gained mummy from {self.name}!\n"
                    msg += attacker.send_out_ability(self, battle)
                if self.ability() == Ability.LINGERING_AROMA and attacker.ability() != Ability.LINGERING_AROMA and attacker.ability_changeable():
                    attacker.ability_id = Ability.LINGERING_AROMA
                    msg += f"{attacker.name} gained lingering aroma from {self.name}!\n"
                    msg += attacker.send_out_ability(self, battle)
                if self.ability() == Ability.GOOEY:
                    msg += attacker.append_speed(-1, attacker=self, source=f"touching {self.name}'s gooey body")
                if self.ability() == Ability.TANGLING_HAIR:
                    msg += attacker.append_speed(-1, attacker=self, source=f"touching {self.name}'s tangled hair")

            # Pickpocket is not included in the protective pads protection
            if (
                self.ability() == Ability.PICKPOCKET
                and not self.held_item.has_item()
                and attacker.held_item.has_item()
                and attacker.held_item.can_remove()
            ):
                if attacker.ability() == Ability.STICKY_HOLD:
                    msg += f"{attacker.name}'s sticky hand kept hold of its item!\n"
                else:
                    attacker.held_item.transfer(self.held_item)
                    msg += f"{attacker.name}'s {self.held_item.name} was stolen!\n"
            # Affects DEFENDER
            if attacker.ability() == Ability.POISON_TOUCH:
                if random.randint(1, 100) <= 30:
                    msg += self.nv.apply_status("poison", battle, attacker=attacker, move=move, source=f"{attacker.name}'s poison touch")
            # Affects BOTH
            if attacker.held_item != "protective-pads":
                if self.ability() == Ability.PERISH_BODY and not attacker.perish_song.active():
                    attacker.perish_song.set_turns(4)
                    self.perish_song.set_turns(4)
                    msg += f"All pokemon will faint after 3 turns from {self.name}'s perish body!\n"
            if self.ability() == Ability.WANDERING_SPIRIT and attacker.ability_changeable() and attacker.ability_giveable():
                msg += f"{attacker.name} swapped abilities with {self.name} because of {self.name}'s wandering spirit!\n"
                self.ability_id, attacker.ability_id = attacker.ability_id, self.ability_id
                ability_name = Ability(self.ability_id).pretty_name
                msg += f"{self.name} acquired {ability_name}!\n"
                msg += self.send_out_ability(attacker, battle)
                ability_name = Ability(attacker.ability_id).pretty_name
                msg += f"{attacker.name} acquired {ability_name}!\n"
                msg += attacker.send_out_ability(self, battle)
        
        return msg, true_damage
    
    def heal(self, health, *, source: str=""):
        """
        Heals a pokemon by a certain amount.
        
        Handles heal-affecting items and abilities, and keeping health within bounds.
        Returns a formatted message.
        """
        msg = ""
        health = max(1, int(health))
        #greater than is used to prevent zygarde's hp incresing form from losing its extra health
        if self.hp >= self.starting_hp:
            return msg
        #safety to prevent errors from ""reviving"" pokes
        if self.hp == 0:
            return msg
        if self.heal_block.active():
            return msg
        health = min(self.starting_hp - self.hp, health)
        self.hp += health
        if source:
            source = f" from {source}"
        msg += f"{self.name} healed {health} hp{source}!\n"
        return msg
    
    def confuse(self, *, attacker=None, move=None, source=""):
        """
        Attempts to confuse this poke.
        
        Returns a formatted message.
        """ 
        if self.substitute and (move is None or move.is_affected_by_substitute()):
            return ""
        if self.confusion.active():
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.OWN_TEMPO:
            return ""
        self.confusion.set_turns(random.randint(2, 5))
        if source:
            source = f" from {source}"
        msg = f"{self.name} is confused{source}!\n"
        if self.held_item.should_eat_berry_status(attacker):
            msg += self.held_item.eat_berry(attacker=attacker, move=move)
        return msg
    
    def flinch(self, *, attacker=None, move=None, source=""):
        """
        Attepts to flinch this poke.
        
        Returns a formatted message.
        """
        msg = ""
        if self.substitute and (move is None or move.is_affected_by_substitute()):
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.INNER_FOCUS:
            return f"{self.name} resisted the urge to flinch with its inner focus!\n"
        self.flinched = True
        if source:
            source = f" from {source}"
        msg += f"{self.name} flinched{source}!\n"
        if self.ability() == Ability.STEADFAST:
            msg += self.append_speed(1, attacker=self, source="its steadfast")
        return msg
        
    def infatuate(self, attacker, *, move=None, source=""):
        """
        Attepts to cause attacker to infatuate this poke.
        
        Returns a formatted message.
        """
        msg = ""
        if source:
            source = f" from {source}"
        if "-x" in (self.gender, attacker.gender):
            return ""
        if self.gender == attacker.gender:
            return ""
        if self.ability(move=move, attacker=attacker) == Ability.OBLIVIOUS:
            return f"{self.name} is too oblivious to fall in love!\n"
        if self.ability(move=move, attacker=attacker) == Ability.AROMA_VEIL:
            return f"{self.name}'s aroma veil protects it from being infatuated!\n"
        self.infatuated = attacker
        msg += f"{self.name} fell in love{source}!\n"
        if self.held_item == "destiny-knot":
            msg += attacker.infatuate(self, source=f"{self.name}'s destiny knot")
        return msg