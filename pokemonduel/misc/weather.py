from .expiring_effect import ExpiringEffect
from ..enums import Ability, ElementType


class Weather(ExpiringEffect):
    """
    The current weather of the battlefield.

    Options:
    -hail
    -sandstorm
    -h-rain
    -rain
    -h-sun
    -sun
    -h-wind
    """

    def __init__(self, battle):
        super().__init__(0)
        self._weather_type = ""
        self.battle = battle

    def _expire_weather(self):
        """Clear the current weather and update Castform forms."""
        self._weather_type = ""
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() == Ability.FORECAST and poke._name in ("Castform-snowy", "Castform-rainy",
                                                                     "Castform-sunny"):
                if poke.form("Castform"):
                    poke.type_ids = [ElementType.NORMAL]

    def next_turn(self):
        """Progresses the weather a turn."""
        if super().next_turn():
            self._expire_weather()
            return True
        return False

    def recheck_ability_weather(self):
        """Checks if strong weather effects from a pokemon with a weather ability need to be removed."""
        maintain_weather = False
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if self._weather_type == "h-wind" and poke.ability() == Ability.DELTA_STREAM:
                maintain_weather = True
            if self._weather_type == "h-sun" and poke.ability() == Ability.DESOLATE_LAND:
                maintain_weather = True
            if self._weather_type == "h-rain" and poke.ability() == Ability.PRIMORDIAL_SEA:
                maintain_weather = True

        if self._weather_type in ("h-wind", "h-sun", "h-rain") and not maintain_weather:
            self._expire_weather()
            return True
        return False

    def get(self):
        """Get the current weather type."""
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() in (Ability.CLOUD_NINE, Ability.AIR_LOCK):
                return ""
        return self._weather_type

    def set(self, weather: str, pokemon):
        """
        Set the weather, lasting a certain number of turns.

        Returns a formatted message indicating any weather change.
        """
        msg = ""
        turns = None
        element = None
        castform = None
        if self._weather_type == weather:
            return ""
        if weather == "hail":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "icy-rock":
                turns = 8
            else:
                turns = 5
            msg += "It starts to hail!\n"
            element = ElementType.ICE
            castform = "Castform-snowy"
        elif weather == "sandstorm":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "smooth-rock":
                turns = 8
            else:
                turns = 5
            msg += "A sandstorm is brewing up!\n"
            element = ElementType.NORMAL
            castform = "Castform"
        elif weather == "rain":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "damp-rock":
                turns = 8
            else:
                turns = 5
            msg += "It starts to rain!\n"
            element = ElementType.WATER
            castform = "Castform-rainy"
        elif weather == "sun":
            if self._weather_type in ("h-rain", "h-sun", "h-wind"):
                return ""
            if pokemon.held_item == "heat-rock":
                turns = 8
            else:
                turns = 5
            msg += "The sunlight is strong!\n"
            element = ElementType.FIRE
            castform = "Castform-sunny"
        elif weather == "h-rain":
            msg += "Heavy rain begins to fall!\n"
            element = ElementType.WATER
            castform = "Castform-rainy"
        elif weather == "h-sun":
            msg += "The sunlight is extremely harsh!\n"
            element = ElementType.FIRE
            castform = "Castform-sunny"
        elif weather == "h-wind":
            msg += "The winds are extremely strong!\n"
            element = ElementType.NORMAL
            castform = "Castform"
        else:
            raise ValueError("unexpected weather")

        t = ElementType(element).name.lower()
        for poke in (self.battle.trainer1.current_pokemon, self.battle.trainer2.current_pokemon):
            if poke is None:
                continue
            if poke.ability() == Ability.FORECAST and poke._name != castform:
                if poke.form(castform):
                    poke.type_ids = [element]
                    msg += f"{poke.name} transformed into a {t} type using its forecast!\n"

        self._weather_type = weather
        # pyrefly: ignore [bad-assignment]
        self._remaining_turns = turns
        return msg
