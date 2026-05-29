import discord
from .trainer_base import Trainer


class MemberTrainer(Trainer):
    """
    Represents a pokemon trainer that is a discord.Member.
    """
    def __init__(self, member: discord.Member, party):
        super().__init__(member.name, party)
        self.id = member.id
        self.member = member

    def is_human(self):
        """Returns True if this trainer is a human player, False if it is an AI."""
        return True
