from ..randoms.random_team_gen import convert_team_to_raw_data, generate_random_team


def generate_npc_team(seed: int = None):
    """
    Generate a random team for the NPC opponent.
    Uses the same random team generation as random battles.
    """
    return generate_random_team(6, seed=seed)

def convert_to_raw_data(team, team_name: str = "NPC Team"):
    """
    Convert generated team to raw_data format compatible with pokemon.create().
    """
    return convert_team_to_raw_data(team, team_name)


async def create_npc_team(ctx, seed: int = None):
    """
    Create a full NPC team ready for battle, including converting to pokemon objects.
    Returns a list of DuelPokemon objects.
    """
    from ...pokemon import create

    team_data = generate_npc_team(seed)
    raw_data = convert_to_raw_data(team_data, "NPC Team")

    team = []
    for pokemon_data in raw_data:
        pokemon = await create(ctx, pokemon_data)
        team.append(pokemon)

    return team