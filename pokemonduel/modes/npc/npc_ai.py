import random
from ...enums import Ability, ElementType, DamageClass
from ...moves import Move


class NPCTeamAI:
    """
    AI brain for NPC battles that plays like a skilled player.
    Makes decisions based on matchups, predictions, and game theory.
    """

    def __init__(self, trainer, opponent):
        self.trainer = trainer
        self.opponent = opponent
        self.battle = None
        self.turn_count = 0

    def set_battle(self, battle):
        """Set the battle context for the AI."""
        self.battle = battle
        self.turn_count += 1

    def _get_type_effectiveness(self, move, defender):
        """Get type effectiveness of a move against defender."""
        if move.damage_class == DamageClass.STATUS:
            return 1.0

        move_type = move.type
        defender_types = defender.type_ids

        effectiveness = 1.0
        # Safely check type effectiveness
        if self.battle and self.battle.type_effectiveness:
            for def_type in defender_types:
                if (move_type, def_type) in self.battle.type_effectiveness:
                    effectiveness *= self.battle.type_effectiveness[(move_type, def_type)] / 100.0

        return effectiveness

    def _calculate_move_score(self, move, defender):
        """Calculate a score for how good a move is."""
        score = 0.0
        attacker = self.trainer.current_pokemon

        # Base score from damage class
        if move.damage_class == DamageClass.STATUS:
            # Status moves have utility value
            score += 10
            if hasattr(move, 'effect') and move.effect == 87:  # Thunder Wave
                score += 15
            elif hasattr(move, 'effect') and move.effect == 38:  # Will-o-wisp
                score += 15
            elif hasattr(move, 'effect') and move.effect == 34:  # Spikes
                score += 20
            elif hasattr(move, 'effect') and move.effect == 372:  # Stealth Rock
                score += 25
            elif hasattr(move, 'effect') and move.effect == 73:  # Light Screen
                score += 10
            elif hasattr(move, 'effect') and move.effect == 74:  # Reflect
                score += 10
            return score

        # Calculate base power score
        base_power = move.power if move.power else 0
        if base_power == 0:
            return 5  # Low score for non-damaging moves without utility

        # STAB bonus
        stab = 1.5 if move.type in attacker.type_ids else 1.0
        score += base_power * stab / 100

        # Type effectiveness
        effectiveness = self._get_type_effectiveness(move, defender)
        if effectiveness >= 4.0:
            score += 50  # Massive bonus for 4x effective
        elif effectiveness >= 2.0:
            score += 30  # Good bonus for 2x effective
        elif effectiveness <= 0.25:
            score -= 30  # Penalty for not very effective
        elif effectiveness == 0:
            score -= 100  # Don't use immune moves

        # Move accuracy penalty
        if move.accuracy and move.accuracy < 80:
            score -= 5

        # High critical hit moves
        if hasattr(move, 'effect') and move.effect == 102:  # Focus Punch
            score += 15

        # Priority moves get bonus in certain situations
        if move.priority > 0:
            our_speed = attacker.get_speed(self.battle)
            opp_speed = defender.get_speed(self.battle)
            if our_speed < opp_speed:
                score += 20  # Priority helps outspeed

        return score

    def _evaluate_switch_in(self, poke_idx):
        """Evaluate how good a switch-in would be against opponent's current pokemon."""
        candidate = self.trainer.party[poke_idx]
        opponent = self.opponent.current_pokemon

        if not candidate or candidate.hp <= 0:
            return -999

        score = 50  # Base score

        # Check if candidate resists opponent's moves (safely)
        if opponent and hasattr(opponent, 'moves') and opponent.moves:
            for move in opponent.moves:
                if move.damage_class == DamageClass.STATUS:
                    continue
                move_type = move.type
                for cand_type in candidate.type_ids:
                    if self.battle and self.battle.type_effectiveness and (move_type, cand_type) in self.battle.type_effectiveness:
                        eff = self.battle.type_effectiveness[(move_type, cand_type)] / 100.0
                        if eff >= 2.0:
                            score += 20
                        elif eff <= 0.5:
                            score -= 15
                        elif eff == 0:
                            score += 30  # Immune!

        # Check if candidate can threaten opponent
        if opponent:
            for move in candidate.moves:
                if move.damage_class == DamageClass.STATUS:
                    continue
                eff = self._get_type_effectiveness(move, opponent)
                if eff >= 2.0:
                    score += 15

        # HP percentage
        hp_percent = candidate.hp / candidate.starting_hp
        score += hp_percent * 20

        return score

    def _should_switch(self):
        """Decide if switching is the best option."""
        if not self.trainer.current_pokemon:
            return None

        current = self.trainer.current_pokemon
        opponent = self.opponent.current_pokemon

        if not opponent:
            return None

        # Check valid switches
        valid_switches = self.trainer.valid_swaps(opponent, self.battle, check_trap=False)
        if not valid_switches:
            return None

        # Check if current pokemon is in danger
        danger_score = 0

        # Check opponent's moves against us (safely handle missing moves)
        if hasattr(opponent, 'moves') and opponent.moves:
            for move in opponent.moves:
                if move.damage_class == DamageClass.STATUS:
                    continue
                eff = self._get_type_effectiveness(move, current)
                if eff >= 4.0:
                    danger_score += 50
                elif eff >= 2.0:
                    danger_score += 25

        # Check if statused
        if current.nv.current:
            danger_score += 20

        # Check if low HP
        if current.hp / current.starting_hp < 0.3:
            danger_score += 30

        # If very dangerous, definitely switch
        if danger_score >= 60:
            # Find best switch
            best_switch = None
            best_score = -999
            for idx in valid_switches:
                score = self._evaluate_switch_in(idx)
                if score > best_score:
                    best_score = score
                    best_switch = idx

            # Only switch if it's a significant improvement
            if best_score > 70:
                return best_switch

        return None

    def choose_lead(self):
        """Choose the best lead Pokemon for the battle start."""
        if not self.trainer.party:
            return 0

        best_idx = 0
        best_score = -999

        for idx, poke in enumerate(self.trainer.party):
            if poke.hp <= 0:
                continue

            score = 50  # Base score

            # Check speed for first turn priority (use raw speed if no battle)
            if self.battle:
                speed = poke.get_speed(self.battle)
            else:
                speed = poke.get_raw_speed()
            score += speed / 10

            # Check for useful moves like hazards
            for move in poke.moves:
                if move.damage_class == DamageClass.STATUS:
                    if hasattr(move, 'effect'):
                        if move.effect == 34:  # Spikes
                            score += 20
                        elif move.effect == 372:  # Stealth Rock
                            score += 25
                        elif move.effect == 38:  # Will-o-wisp
                            score += 15

            # Prefer resists for common types (skip if no battle)
            if self.battle and self.battle.type_effectiveness:
                common_types = [ElementType.WATER, ElementType.FIRE, ElementType.ELECTRIC, ElementType.GROUND]
                for ctype in common_types:
                    for ptype in poke.type_ids:
                        if (ctype, ptype) in self.battle.type_effectiveness:
                            eff = self.battle.type_effectiveness[(ctype, ptype)] / 100.0
                            if eff >= 2.0:
                                score += 10

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def choose_move(self):
        """Choose the best move for the current turn."""
        status_code, movedata = self.trainer.valid_moves(self.opponent.current_pokemon)

        if status_code == "forced":
            return movedata, None

        if status_code == "struggle":
            return Move.struggle(), None

        # Get current pokemon and opponent
        pokemon = self.trainer.current_pokemon
        opponent = self.opponent.current_pokemon

        if not pokemon or not opponent:
            # Fallback - just pick first valid move
            for idx in movedata:
                return pokemon.moves[idx], None

        # Calculate scores for all moves
        move_scores = []
        for idx in movedata:
            move = pokemon.moves[idx]
            score = self._calculate_move_score(move, opponent)
            move_scores.append((idx, score))

        # Sort by score descending
        move_scores.sort(key=lambda x: x[1], reverse=True)

        # Add some randomness - top 2 moves with weighted probability
        if len(move_scores) >= 2 and random.random() < 0.15:
            # 15% chance to pick second best (to be less predictable)
            chosen_idx = move_scores[1][0]
        else:
            chosen_idx = move_scores[0][0]

        # Check if switching is better
        switch_idx = self._should_switch()
        if switch_idx is not None:
            return pokemon.moves[chosen_idx], switch_idx

        return pokemon.moves[chosen_idx], None

    def choose_switch(self, mid_turn=False):
        """Choose the best switch-in."""
        return self._should_switch()