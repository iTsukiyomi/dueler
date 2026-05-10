from ..misc import ExpiringEffect


class DuelPokemonSendOut:
    """Pokemon send out and remove logic."""

    def send_out(self, otherpoke, battle):
        """Initialize a poke upon first sending it out."""
        self.ever_sent_out = True
        self.flinched = False

        illusion_options = [x for x in self.owner.party if x is not self and x.hp > 0]
        if self.ability() == Ability.ILLUSION and illusion_options:
            self.illusion__name = self._name
            self.illusion_name = self.name
            self._name = illusion_options[-1]._name
            self.name = illusion_options[-1].name

        if self._name == "Pikachu":
            msg = f"{self.name}, I choose you!\n"
        else:
            msg = f"{self.owner.name} sent out {self.name}!\n"

        if otherpoke is not None:
            otherpoke.trapping = False
            otherpoke.octolock = False
            otherpoke.bind.set_turns(0)

        if self.owner.baton_pass is not None:
            msg += f"{self.name} carries on the baton!\n"
            self.owner.baton_pass.apply(self)
            self.owner.baton_pass = None

        if self.owner.next_substitute:
            self.substitute = self.owner.next_substitute
            self.owner.next_substitute = 0

        if self.owner.toxic_spikes and self.grounded(battle) and ElementType.POISON in self.type_ids:
            self.owner.toxic_spikes = 0
            msg += f"{self.name} absorbed the toxic spikes!\n"
        if self.held_item != "heavy-duty-boots":
            if self.grounded(battle):
                if self.owner.spikes:
                    damage = self.starting_hp // (10 - (2 * self.owner.spikes))
                    msg += self.damage(damage, battle, source="spikes")
                if self.owner.toxic_spikes == 1:
                    msg += self.nv.apply_status("poison", battle, source="toxic spikes")
                elif self.owner.toxic_spikes == 2:
                    msg += self.nv.apply_status("b-poison", battle, source="toxic spikes")
                if self.owner.sticky_web:
                    msg += self.append_speed(-1, source="the sticky web")
            if self.owner.stealth_rock:
                effective = self.effectiveness(ElementType.ROCK, battle)
                if effective:
                    damage = self.starting_hp // (32 // (4 * effective))
                    msg += self.damage(int(damage), battle, source="stealth rock")
            if self.owner.sticky_barb and self.hp > 0:
                msg += self.damage(self.starting_hp // 8, battle, source="its Sticky Barb")
            if self.owner.rough_skin_user is not None and self.hp > 0:
                msg += self.damage(self.starting_hp // 8, battle, source=f"{self.owner.rough_skin_user.name}'s Rough Skin")
            if self.owner.minus_user is not None and self.ability() in (Ability.PLUS, Ability.MINUS):
                msg += self.append_spatk(1, source="its Plus/Minus")

        self.held_item.battle = battle
        msg += self.held_item.activate_on_switch_in(battle)
        if self.ability() == Ability.RECEIVER and self.owner.last_fainted_pokemon is not None:
            if self.owner.last_fainted_pokemon.ability_id != Ability.RECEIVER:
                self.ability_id = self.owner.last_fainted_pokemon.ability_id
                msg += f"{self.name} received {self.ability().pretty_name}!\n"

        msg += self.send_out_ability(otherpoke, battle)
        return msg

    def send_out_ability(self, otherpoke, battle):
        """Handle abilities that trigger on send out."""
        msg = ""
        if self.ability() == Ability.INTIMIDATE and otherpoke is not None:
            msg += otherpoke.append_attack(-1, attacker=self, source=f"{self.name}'s Intimidate")
        if self.ability() == Ability.DOWNLOAD and otherpoke is not None:
            if otherpoke.defense <= otherpoke.spdef:
                msg += self.append_spatk(1, source="its Download")
            else:
                msg += self.append_attack(1, source="its Download")
        if self.ability() == Ability.ANTICIPATION and otherpoke is not None:
            msg += f"{self.name} shuddered!\n"
        if self.ability() == Ability.FOREWARN and otherpoke is not None:
            for move in otherpoke.moves:
                if move.damage_class != DamageClass.STATUS:
                    msg += f"{self.name} foresaw {move.pretty_name}!\n"
                    break
        if self.ability() == Ability.PRESSURE and otherpoke is not None:
            msg += f"{self.name} is exerting its pressure!\n"
        if self.ability() == Ability.FRISK and otherpoke is not None:
            if otherpoke.held_item != "none":
                msg += f"{self.name} frisked {otherpoke.name} and found {otherpoke.held_item}!\n"
        if self.ability() == Ability.IMPOSTER:
            if otherpoke is not None:
                self.transform(otherpoke)
        if self.ability() == Ability.ILLUSION and self.illusion_name is not None:
            msg += f"{self.name} transformed into {self.illusion_name}!\n"
        if self.ability() == Ability.SCREAM_SURF:
            if battle.terrain.item == "electric":
                msg += self.append_speed(1, source="its Scream Surf")
        if self.ability() == Ability.TURBOBLAZE and battle.weather.get() == "sun":
            msg += self.append_speed(1, source="its Turboblaze")
        if self.ability() == Ability.TERAVOLT and battle.weather.get() == "sun":
            msg += self.append_speed(1, source="its Teravolt")

        if otherpoke is not None:
            if otherpoke.ability() == Ability.INTIMIDATE:
                msg += self.append_attack(-1, attacker=otherpoke, source=f"{otherpoke.name}'s Intimidate")
            if otherpoke.ability() == Ability.DOWNLOAD:
                if self.defense <= self.spdef:
                    msg += otherpoke.append_spatk(1, source="its Download")
                else:
                    msg += otherpoke.append_attack(1, source="its Download")
            if otherpoke.ability() == Ability.PRESSURE:
                msg += f"{otherpoke.name} is exerting its pressure!\n"
            if otherpoke.ability() == Ability.FRISK:
                if self.held_item != "none":
                    msg += f"{otherpoke.name} frisked {self.name} and found {self.held_item}!\n"
            if otherpoke.ability() == Ability.IMPOSTER:
                if not self.is_holding_transform():
                    otherpoke.transform(self)
            if otherpoke.ability() == Ability.CONTRARY and self.attack_stage != 0:
                msg += otherpoke.append_attack(-self.attack_stage, source="Contrary")
            if otherpoke.ability() == Ability.CONTRARY and self.defense_stage != 0:
                msg += otherpoke.append_defense(-self.defense_stage, source="Contrary")
            if otherpoke.ability() == Ability.CONTRARY and self.spatk_stage != 0:
                msg += otherpoke.append_spatk(-self.spatk_stage, source="Contrary")
            if otherpoke.ability() == Ability.CONTRARY and self.spdef_stage != 0:
                msg += otherpoke.append_spdef(-self.spdef_stage, source="Contrary")
            if otherpoke.ability() == Ability.CONTRARY and self.speed_stage != 0:
                msg += otherpoke.append_speed(-self.speed_stage, source="Contrary")

        if otherpoke is not None and otherpoke.ability() != Ability.ILLUSION:
            msg += self.send_out_effect(otherpoke, battle)
        return msg

    def remove(self, battle, *, fainted=False):
        """Remove a pokemon from battle."""
        msg = ""
        if not fainted:
            if self.ability() == Ability.REGRESSION:
                if self.illusion__name is not None:
                    self._name = self.illusion__name
                    self.name = self.illusion_name
                    self.illusion__name = None
                    self.illusion_name = None
                    msg += f"{self.name}'s Illusion ended!\n"
        else:
            msg += f"{self.name} fainted!\n"
            self.owner.last_fainted_pokemon = self

        if self.ability() in (Ability.ILLUSION, Ability.IMPOSTER):
            self.illusion__name = None
            self.illusion_name = None

        self.owner.mid_turn_remove = True

        for otherpoke in self.owner.party:
            if otherpoke is not self and otherpoke.hp > 0:
                otherpoke.trapping = False
                otherpoke.bind.set_turns(0)
                otherpoke.octolock = False

        if self.ability() == Ability.ORICHALCUM_PULSE and battle.weather.get() in ("sun", "h-sun"):
            battle.weather.set("sun", self)

        return msg