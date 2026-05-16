"""
NPC AI Training Script - Trains the ML model via self-play.
Run this script repeatedly until accuracy reaches 85%+
"""
import os
import sys
import random
import numpy as np
import json
from copy import deepcopy

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "learning_data")
MODEL_PATH = os.path.join(DATA_DIR, "npc_model.pkl")
SCALER_PATH = os.path.join(DATA_DIR, "scaler.pkl")
DECISIONS_PATH = os.path.join(DATA_DIR, "decisions.json")

os.makedirs(DATA_DIR, exist_ok=True)

# Element types
ELEMENT_TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel", "fairy"
]

# Simple type chart
TYPE_CHART = {
    ("fire", "grass"): 2.0, ("fire", "ice"): 2.0, ("fire", "bug"): 2.0, ("fire", "steel"): 0.5,
    ("water", "fire"): 2.0, ("water", "ground"): 2.0, ("water", "rock"): 0.5, ("water", "dragon"): 0.5,
    ("electric", "water"): 2.0, ("electric", "flying"): 2.0, ("electric", "ground"): 0, ("electric", "grass"): 0.5,
    ("grass", "water"): 2.0, ("grass", "ground"): 2.0, ("grass", "rock"): 0.5, ("grass", "fire"): 0.5,
    ("ice", "grass"): 2.0, ("ice", "ground"): 2.0, ("ice", "flying"): 2.0, ("ice", "dragon"): 0.5,
    ("fighting", "normal"): 2.0, ("fighting", "rock"): 0.5, ("fighting", "ghost"): 0, ("fighting", "bug"): 0.5,
    ("poison", "grass"): 2.0, ("poison", "fairy"): 0.5, ("poison", "ghost"): 0.5,
    ("ground", "fire"): 2.0, ("ground", "electric"): 2.0, ("ground", "poison"): 0.5, ("ground", "rock"): 0.5,
    ("flying", "grass"): 2.0, ("flying", "fighting"): 2.0, ("flying", "electric"): 0.5, ("flying", "rock"): 0.5,
    ("psychic", "fighting"): 2.0, ("psychic", "poison"): 0.5, ("psychic", "dark"): 0,
    ("bug", "grass"): 2.0, ("bug", "psychic"): 0.5, ("bug", "ghost"): 0.5, ("bug", "dark"): 0.5,
    ("rock", "fire"): 2.0, ("rock", "ice"): 2.0, ("rock", "flying"): 2.0, ("rock", "bug"): 0.5,
    ("ghost", "psychic"): 2.0, ("ghost", "ghost"): 0, ("ghost", "normal"): 0,
    ("dragon", "dragon"): 2.0, ("dragon", "steel"): 0.5,
    ("dark", "psychic"): 2.0, ("dark", "ghost"): 2.0, ("dark", "dark"): 0.5,
    ("steel", "ice"): 2.0, ("steel", "rock"): 0.5, ("steel", "fire"): 0.5, ("steel", "steel"): 0.5,
    ("fairy", "fighting"): 2.0, ("fairy", "dragon"): 2.0, ("fairy", "dark"): 0.5,
}

# Damage moves with variety
DAMAGE_MOVES = [
    {"name": "Tackle", "move_type": "normal", "power": 40, "accuracy": 100},
    {"name": "Ember", "move_type": "fire", "power": 40, "accuracy": 100},
    {"name": "Water Gun", "move_type": "water", "power": 40, "accuracy": 100},
    {"name": "Vine Whip", "move_type": "grass", "power": 45, "accuracy": 100},
    {"name": "Thunder Shock", "move_type": "electric", "power": 40, "accuracy": 100},
    {"name": "Ice Beam", "move_type": "ice", "power": 90, "accuracy": 100},
    {"name": "Flamethrower", "move_type": "fire", "power": 90, "accuracy": 100},
    {"name": "Hydro Pump", "move_type": "water", "power": 110, "accuracy": 80},
    {"name": "Thunderbolt", "move_type": "electric", "power": 90, "accuracy": 100},
    {"name": "Earthquake", "move_type": "ground", "power": 100, "accuracy": 100},
    {"name": "Psychic", "move_type": "psychic", "power": 90, "accuracy": 100},
    {"name": "Draco Meteor", "move_type": "dragon", "power": 130, "accuracy": 90},
    {"name": "Close Combat", "move_type": "fighting", "power": 120, "accuracy": 100},
    {"name": "Stone Edge", "move_type": "rock", "power": 100, "accuracy": 80},
    {"name": "Shadow Ball", "move_type": "ghost", "power": 80, "accuracy": 100},
    {"name": "Sludge Bomb", "move_type": "poison", "power": 90, "accuracy": 100},
]

# Status moves - important for proper learning
STATUS_MOVES = [
    {"name": "Toxic", "move_type": "poison", "effect": "toxic"},
    {"name": "Will-O-Wisp", "move_type": "fire", "effect": "burn"},
    {"name": "Thunder Wave", "move_type": "electric", "effect": "paralyze"},
    {"name": "Spikes", "move_type": "ground", "effect": "spikes"},
    {"name": "Stealth Rock", "move_type": "rock", "effect": "stealth_rock"},
    {"name": "Toxic Spikes", "move_type": "poison", "effect": "toxic_spikes"},
    {"name": "Defog", "move_type": "flying", "effect": "defog"},
    {"name": "Recover", "move_type": "normal", "effect": "heal"},
    {"name": "Swords Dance", "move_type": "normal", "effect": "atk_boost"},
    {"name": "Calm Mind", "move_type": "psychic", "effect": "spatk_boost"},
]


class SimPokemon:
    def __init__(self, name, types, hp, atk, dfs, spa, spd, spd_stat, moves):
        self.name = name
        self.types = types
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.dfs = dfs
        self.spa = spa
        self.spd = spd
        self.spd_stat = spd_stat
        self.moves = moves
        self.atk_stage = 0
        self.dfs_stage = 0
        self.spa_stage = 0
        self.spd_stage = 0
        self.status = None

    def alive(self):
        return self.hp > 0

    def get_speed(self):
        spd = self.spd_stat
        if self.status == "paralyze":
            spd *= 0.5
        return spd


class SimMove:
    def __init__(self, name, move_type=None, power=None, accuracy=None, effect=None):
        self.name = name
        self.type = move_type if move_type else "normal"
        self.power = power if power else 0
        self.accuracy = accuracy if accuracy else 100
        self.effect = effect

    def is_status(self):
        return self.power == 0

    def get_effectiveness(self, target_types):
        eff = 1.0
        for tt in target_types:
            key = (self.type, tt)
            if key in TYPE_CHART:
                eff *= TYPE_CHART[key]
        return eff


class SimTrainer:
    def __init__(self, name, party):
        self.name = name
        self.party = party
        self.current = party[0]
        self.spikes = 0
        self.toxic_spikes = 0
        self.stealth_rock = False
        self.sticky_web = False


class BattleSimulator:
    def __init__(self):
        self.decisions = []

    def generate_pokemon(self, include_status=True):
        name = f"P_{random.randint(1000, 9999)}"
        types = [random.choice(ELEMENT_TYPES)]
        if random.random() < 0.3:
            types.append(random.choice(ELEMENT_TYPES))

        hp = random.randint(90, 140)
        atk = random.randint(70, 120)
        dfs = random.randint(70, 120)
        spa = random.randint(70, 120)
        spd_stat = random.randint(70, 120)
        spd = random.randint(60, 130)

        moves = []
        # Add 2-4 damage moves
        num_damage = random.randint(2, 4)
        damage_pool = random.sample(DAMAGE_MOVES, min(num_damage, len(DAMAGE_MOVES)))
        for m in damage_pool:
            moves.append(SimMove(**m))

        # Add status moves (important for learning!)
        if include_status and random.random() < 0.5:
            num_status = random.randint(1, 2)
            status_pool = random.sample(STATUS_MOVES, min(num_status, len(STATUS_MOVES)))
            for m in status_pool:
                moves.append(SimMove(**m))

        return SimPokemon(name, types, hp, atk, dfs, spa, spd_stat, spd, moves)

    def generate_party(self, size=3, include_status=True):
        return [self.generate_pokemon(include_status) for _ in range(size)]

    def encode_state(self, attacker, defender, trainer, opponent):
        """Encode battle state as feature vector."""
        features = []

        # Our Pokemon
        features.append(attacker.hp / attacker.max_hp)
        features.append(attacker.atk_stage / 6)
        features.append(attacker.dfs_stage / 6)
        features.append(attacker.spa_stage / 6)
        features.append(attacker.spd_stage / 6)
        features.append(1 if attacker.status else 0)
        features.append(attacker.atk / 150)
        features.append(attacker.spa / 150)
        features.append(attacker.dfs / 150)
        features.append(attacker.spd / 150)
        features.append(attacker.spd_stat / 150)

        # Count move types
        num_attacks = sum(1 for m in attacker.moves if m.power > 0)
        num_status = sum(1 for m in attacker.moves if m.power == 0)
        features.append(num_attacks / 4)
        features.append(num_status / 4)

        # Strongest move power
        max_power = max((m.power for m in attacker.moves), default=0)
        features.append(max_power / 150)

        # Opponent
        features.append(defender.hp / defender.max_hp)
        features.append(defender.atk_stage / 6)
        features.append(defender.dfs_stage / 6)
        features.append(defender.spa_stage / 6)
        features.append(defender.spd_stage / 6)
        features.append(1 if defender.status else 0)
        features.append(defender.atk / 150)
        features.append(defender.spa / 150)
        features.append(defender.dfs / 150)
        features.append(defender.spd / 150)
        features.append(defender.spd_stat / 150)

        # Type matchups
        best_offense = 0.5
        for move in attacker.moves:
            if move.power == 0:
                continue
            eff = move.get_effectiveness(defender.types)
            best_offense = max(best_offense, min(eff / 4, 1.0))
        features.append(best_offense)

        worst_defense = 0.5
        for move in defender.moves:
            if move.power == 0:
                continue
            eff = move.get_effectiveness(attacker.types)
            worst_defense = max(worst_defense, min(eff / 4, 1.0))
        features.append(worst_defense)

        # Resist/weakness count
        resist = sum(1 for at in attacker.types for dt in defender.types
                    if TYPE_CHART.get((at, dt), 1) <= 0.5)
        weak = sum(1 for at in attacker.types for dt in defender.types
                  if TYPE_CHART.get((at, dt), 1) >= 2.0)
        features.append(min(resist / 3, 1.0))
        features.append(min(weak / 3, 1.0))

        # Field state
        features.append(trainer.spikes / 3)
        features.append(trainer.toxic_spikes / 2)
        features.append(1 if trainer.stealth_rock else 0)
        features.append(opponent.spikes / 3)
        features.append(opponent.toxic_spikes / 2)
        features.append(1 if opponent.stealth_rock else 0)
        features.append(len([p for p in trainer.party if p.alive()]) / 6)
        features.append(len([p for p in opponent.party if p.alive()]) / 6)

        # HP totals
        our_hp = sum(p.hp for p in trainer.party if p.alive()) / max(sum(p.max_hp for p in trainer.party), 1)
        opp_hp = sum(p.hp for p in opponent.party if p.alive()) / max(sum(p.max_hp for p in opponent.party), 1)
        features.append(our_hp)
        features.append(opp_hp)

        # Switch options
        valid_switches = [p for p in trainer.party if p is not trainer.current and p.alive()]
        features.append(len(valid_switches) / 5)  # 40th feature
        features.append(1 if len(valid_switches) > 0 else 0)  # 41st feature (can switch)
        # 42nd feature: party size indicator
        features.append(len(trainer.party) / 6)

        return features

    def get_optimal_action(self, attacker, defender, trainer, opponent):
        """
        Determine the optimal action - MUST include all 3 action types.
        Returns: 0 = attack, 1 = switch, 2 = status
        """
        # Calculate threats
        worst_threat = 0
        for move in defender.moves:
            if move.power == 0:
                continue
            eff = move.get_effectiveness(attacker.types)
            worst_threat = max(worst_threat, eff)

        hp_percent = attacker.hp / attacker.max_hp

        # Check if should SWITCH
        should_switch = False

        # Low HP check
        if hp_percent < 0.3:
            should_switch = True

        # Very bad matchup (4x or immune and low HP)
        elif worst_threat >= 4.0 and hp_percent < 0.5:
            should_switch = True

        # Check for better switch option
        if not should_switch:
            for poke in trainer.party:
                if poke is attacker or not poke.alive():
                    continue
                switch_worst = max(
                    (m.get_effectiveness(poke.types) for m in defender.moves if m.power > 0),
                    default=0
                )
                # If switch would significantly reduce threat
                if switch_worst < worst_threat * 0.5 and hp_percent < 0.6:
                    should_switch = True
                    break

        if should_switch:
            return 1  # SWITCH

        # Check STATUS move
        has_status_move = False
        for move in attacker.moves:
            if move.power == 0:  # Status move
                has_status_move = True

                # Check if we should use status move
                if move.effect in ["spikes", "stealth_rock", "toxic_spikes"]:
                    # Only use hazards if beneficial
                    if move.effect == "spikes" and trainer.spikes < 3 and not trainer.stealth_rock:
                        return 2  # STATUS
                    elif move.effect == "stealth_rock" and not trainer.stealth_rock:
                        return 2  # STATUS
                    elif move.effect == "toxic_spikes" and trainer.toxic_spikes < 2:
                        return 2  # STATUS

                elif move.effect in ["toxic", "burn", "paralyze"]:
                    # Only status if opponent isn't already statused
                    if not defender.status:
                        return 2  # STATUS

                elif move.effect == "heal":
                    # Only heal if damaged enough
                    if hp_percent < 0.7:
                        return 2  # STATUS

                elif move.effect == "atk_boost":
                    if hp_percent > 0.5:
                        return 2  # STATUS

        # Default to ATTACK
        return 0

    def simulate_battle(self):
        """Simulate a battle and collect training data."""
        party1 = self.generate_party(3, include_status=True)
        party2 = self.generate_party(3, include_status=True)

        t1 = SimTrainer("AI_1", party1)
        t2 = SimTrainer("AI_2", party2)

        turn = 0
        max_turns = 50

        while turn < max_turns:
            if not any(p.alive() for p in party1):
                return 1, t1, t2
            if not any(p.alive() for p in party2):
                return 0, t1, t2

            # Revive dead pokemon
            for trainer in [t1, t2]:
                if not trainer.current.alive():
                    for poke in trainer.party:
                        if poke.alive():
                            trainer.current = poke
                            break

            # Collect decision data
            if t1.current.alive() and t2.current.alive():
                # Player 1 decision
                feat1 = self.encode_state(t1.current, t2.current, t1, t2)
                opt1 = self.get_optimal_action(t1.current, t2.current, t1, t2)
                self.decisions.append((feat1, opt1))

                # Player 2 decision
                feat2 = self.encode_state(t2.current, t1.current, t2, t1)
                opt2 = self.get_optimal_action(t2.current, t1.current, t2, t1)
                self.decisions.append((feat2, opt2))

            # Execute turn
            self._execute_turn(t1, t2)
            turn += 1

        return random.randint(0, 1), t1, t2

    def _execute_turn(self, t1, t2):
        """Execute one turn."""
        p1, p2 = t1.current, t2.current

        # Decide actions
        action1 = self.get_optimal_action(p1, p2, t1, t2)
        action2 = self.get_optimal_action(p2, p1, t2, t1)

        # Execute in speed order
        if p1.get_speed() >= p2.get_speed():
            self._execute_action(t1, t2, action1, p1, p2)
            if p2.alive():
                self._execute_action(t2, t1, action2, p2, p1)
        else:
            self._execute_action(t2, t1, action2, p2, p1)
            if p1.alive():
                self._execute_action(t1, t2, action1, p1, p2)

        # End of turn damage
        for poke, trainer in [(p1, t1), (p2, t2)]:
            if trainer.stealth_rock and poke.alive():
                poke.hp -= poke.max_hp * 0.125
            if trainer.spikes > 0 and poke.alive():
                poke.hp -= poke.max_hp * trainer.spikes / 24

    def _execute_action(self, attacker, defender, action, attacker_poke, defender_poke):
        """Execute a single action."""
        if action == 1:  # SWITCH
            best = None
            best_score = -999
            for poke in attacker.party:
                if poke is attacker_poke or not poke.alive():
                    continue
                score = 0
                for move in defender_poke.moves:
                    if move.power == 0:
                        continue
                    eff = move.get_effectiveness(poke.types)
                    if eff <= 0.5:
                        score += 20
                    elif eff >= 2.0:
                        score -= 20
                score += poke.hp / poke.max_hp * 20
                if score > best_score:
                    best_score = score
                    best = poke
            if best:
                attacker.current = best

        elif action == 2:  # STATUS
            for move in attacker_poke.moves:
                if move.power > 0:
                    continue
                if move.effect in ["toxic", "burn", "paralyze"]:
                    if not defender_poke.status:
                        defender_poke.status = move.effect
                        break
                elif move.effect == "spikes" and attacker.spikes < 3:
                    attacker.spikes += 1
                    break
                elif move.effect == "stealth_rock" and not attacker.stealth_rock:
                    attacker.stealth_rock = True
                    break
                elif move.effect == "heal":
                    attacker_poke.hp = min(attacker_poke.max_hp, attacker_poke.hp + attacker_poke.max_hp * 0.5)
                    break
                elif move.effect in ["atk_boost"]:
                    attacker_poke.atk_stage = min(6, attacker_poke.atk_stage + 2)
                    break

        else:  # ATTACK (0)
            best_move = None
            best_score = -999
            for move in attacker_poke.moves:
                if move.power == 0:
                    continue
                score = move.power
                eff = move.get_effectiveness(defender_poke.types)
                score *= eff
                if move.type in attacker_poke.types:
                    score *= 1.5
                if move.accuracy < 100:
                    score *= (move.accuracy / 100)
                if score > best_score:
                    best_score = score
                    best_move = move

            if best_move:
                damage = self._calc_damage(best_move, attacker_poke, defender_poke)
                defender_poke.hp -= damage

    def _calc_damage(self, move, attacker, defender):
        """Calculate damage."""
        atk = attacker.atk * (1 + attacker.atk_stage / 6 * 0.5)
        dfs = defender.dfs * (1 + defender.dfs_stage / 6 * 0.5)
        stab = 1.5 if move.type in attacker.types else 1.0
        eff = move.get_effectiveness(defender.types)
        crit = 1.5 if random.random() < 0.125 else 1.0
        rand = random.uniform(0.85, 1.0)

        damage = ((2 * 50 / 5 + 2) * move.power * atk / dfs / 50 + 2) * stab * eff * crit * rand
        return max(1, int(damage))

    def collect_decisions(self, num_battles=1000):
        """Collect training decisions."""
        self.decisions = []
        for i in range(num_battles):
            self.simulate_battle()
            if (i + 1) % 100 == 0:
                print(f"Simulated {i + 1} battles...")

        print(f"Collected {len(self.decisions)} decision samples")
        return self.decisions


class AITrainer:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.decisions = []
        self.load_data()

    def load_data(self):
        if os.path.exists(DECISIONS_PATH):
            try:
                with open(DECISIONS_PATH, 'r') as f:
                    self.decisions = json.load(f)
                print(f"Loaded {len(self.decisions)} historical decisions")
            except Exception:
                pass

    def save_data(self):
        try:
            with open(DECISIONS_PATH, 'w') as f:
                json.dump(self.decisions[-15000:], f)
        except Exception:
            pass

    def train(self, iterations=5, battles_per_iter=500):
        from sklearn.neural_network import MLPClassifier
        from sklearn.preprocessing import StandardScaler
        import joblib

        simulator = BattleSimulator()

        for iteration in range(iterations):
            print(f"\n=== Training Iteration {iteration + 1}/{iterations} ===")

            print("Collecting battle data...")
            new_decisions = simulator.collect_decisions(battles_per_iter)
            self.decisions.extend(new_decisions)

            if len(self.decisions) > 15000:
                self.decisions = self.decisions[-15000:]

            X = np.array([d[0] for d in self.decisions])
            y = np.array([d[1] for d in self.decisions])

            print(f"Total training samples: {len(X)}")
            print(f"Action distribution: {np.bincount(y.astype(int), minlength=3)}")

            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            print("Training neural network...")
            self.model = MLPClassifier(
                hidden_layer_sizes=(256, 128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                learning_rate='adaptive',
                learning_rate_init=0.001,
                max_iter=1000,
                early_stopping=True,
                validation_fraction=0.15,
                n_iter_no_change=30,
                random_state=42
            )

            self.model.fit(X_scaled, y)

            train_acc = self.model.score(X_scaled, y)
            print(f"Training accuracy: {train_acc:.1%}")

            # Cross-validation
            try:
                from sklearn.model_selection import cross_val_score
                cv_scores = cross_val_score(
                    MLPClassifier(hidden_layer_sizes=(256, 128, 64, 32), max_iter=300, random_state=42),
                    X_scaled, y, cv=5, scoring='accuracy'
                )
                accuracy = cv_scores.mean()
                print(f"Cross-validation accuracy: {accuracy:.1%} (+/- {cv_scores.std():.1%})")

                if accuracy >= 0.85:
                    print(f"\n*** ACHIEVED {accuracy:.1%} ACCURACY - TARGET REACHED! ***")
                    break

            except Exception as e:
                print(f"Cross-validation failed: {e}")

            self.save_data()
            self.save_model()

        return accuracy if 'accuracy' in dir() else train_acc

    def save_model(self):
        import joblib
        if self.model and self.scaler:
            try:
                joblib.dump(self.model, MODEL_PATH)
                joblib.dump(self.scaler, SCALER_PATH)
                print(f"Model saved to {MODEL_PATH}")
            except Exception as e:
                print(f"Failed to save model: {e}")


def main():
    print("=" * 60)
    print("NPC AI Training - Self-Play Machine Learning")
    print("=" * 60)

    trainer = AITrainer()

    target_accuracy = 0.85
    current_accuracy = 0

    while current_accuracy < target_accuracy:
        print(f"\nTraining for accuracy >= {target_accuracy:.0%}...")
        current_accuracy = trainer.train(iterations=3, battles_per_iter=500)

        if current_accuracy >= target_accuracy:
            print(f"\n*** SUCCESS: Achieved {current_accuracy:.1%} accuracy! ***")
            break

        print(f"\nCurrent accuracy: {current_accuracy:.1%}")
        print("Retraining with more data...")

    trainer.save_model()
    trainer.save_data()

    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {MODEL_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()