import random
from ..enums import Ability, DamageClass, ElementType


class MovePower:
    """Power calculation for moves."""

    def get_power(self, attacker, defender, battle):
        """Get the power of this move."""
        if self.damage_class == DamageClass.STATUS:
            return 0

        power = self.power
        if power is None:
            power = 0

        if self.effect == 70:
            power = attacker.hp * 10 // attacker.starting_hp
            if power == 0:
                power = 1

        if self.effect == 74:
            power = attacker.hp * 10 // attacker.starting_hp
            if power == 0:
                power = 1

        if self.effect == 75:
            power = (attacker.starting_hp - attacker.hp) * 10 // attacker.starting_hp
            if power == 0:
                power = 1

        if self.effect == 76:
            power = (attacker.starting_hp - attacker.hp) * 10 // attacker.starting_hp
            if power == 0:
                power = 1

        if self.effect == 79:
            power = attacker.hp * 10 // attacker.starting_hp
            if power == 0:
                power = 1

        if self.effect == 221:
            if defender.nv.current in ("paralysis", "freeze", "sleep") or defender.confusion.active():
                power = 120
            elif defender.nv.current == "poison":
                power = 80
            else:
                power = 50

        if self.effect == 225:
            if attacker.ability() == Ability.RECKLESS:
                power = 90
            else:
                power = 70

        if self.effect == 102:
            power = 120
            if attacker.ability() == Ability.RECKLESS:
                power = 90

        if self.effect == 148:
            power = 80
            if attacker.ability() == Ability.RECKLESS:
                power = 60

        if self.effect == 242:
            power = 120
            if attacker.ability() == Ability.RECKLESS:
                power = 90

        if self.effect == 3:
            if defender.nv.current == "paralysis":
                power = 100
            elif defender.nv.current == "sleep" or defender.confusion.active():
                power = 80
            elif defender.nv.current == "freeze":
                power = 50
            else:
                power = 20

        if self.effect == 318:
            power = 70 + (attacker.attack_stage - defender.defense_stage) * 10
            if power < 20:
                power = 20
            if power > 150:
                power = 150

        if self.effect == 319:
            power = 70 + (attacker.spatk_stage - defender.spdef_stage) * 10
            if power < 20:
                power = 20
            if power > 150:
                power = 150

        if self.effect == 89:
            power = 40 + (attacker.attack_stage * 10)

        if self.effect == 90:
            power = 40 + (attacker.spatk_stage * 10)

        if self.effect == 336:
            power = 40 + (defender.attack_stage * 10)

        if self.effect == 337:
            power = 40 + (defender.spatk_stage * 10)

        if self.effect == 174:
            power = 50 + (attacker.positive_stat_count() * 30)

        if self.effect == 173:
            power = 50 + (attacker.attack_stage * 30)

        if self.effect == 268:
            power = 40 + (attacker.attack_stage * 30)

        if self.effect == 267:
            power = 40 + (attacker.spatk_stage * 30)

        if self.effect == 189:
            if attacker.attack_stage >= defender.defense_stage:
                power = 150
            else:
                power = 50

        if self.effect == 190:
            if attacker.spatk_stage >= defender.spdef_stage:
                power = 150
            else:
                power = 50

        if self.effect == 191:
            power = 20 * (attacker.attack_stage + 6)
            if power > 200:
                power = 200

        if self.effect == 246:
            power = 20 * (attacker.spatk_stage + 6)
            if power > 200:
                power = 200

        if self.effect == 217:
            power = 20 * (defender.attack_stage + 6)
            if power > 200:
                power = 200

        if self.effect == 218:
            power = 20 * (defender.spatk_stage + 6)
            if power > 200:
                power = 200

        if self.effect == 38:
            if attacker.nv.current == "sleep":
                power = 200
            else:
                power = 50

        if self.effect == 271:
            if attacker.nv.current == "sleep":
                power = 200
            else:
                power = 50

        if self.effect == 39:
            if attacker.nv.current in ("paralysis", "freeze", "sleep") or attacker.confusion.active():
                power = 100
            elif attacker.nv.current == "poison":
                power = 65
            else:
                power = 40

        if self.effect == 67:
            if attacker.nv.burn():
                power = 130
            else:
                power = 40

        if self.effect == 68:
            if attacker.nv.burn():
                power = 130
            else:
                power = 40

        if self.effect == 59:
            if attacker.nv.poison():
                power = 130
            else:
                power = 40

        if self.effect == 61:
            if attacker.nv.paralysis():
                power = 130
            else:
                power = 40

        if self.effect == 118:
            if attacker.hp <= attacker.starting_hp // 3:
                power = 200
            elif attacker.hp <= attacker.starting_hp // 2:
                power = 150
            else:
                power = 100

        if self.effect == 216:
            if defender.hp >= defender.starting_hp // 2:
                power = 40
            elif defender.hp >= defender.starting_hp // 4:
                power = 80
            else:
                power = 120

        if self.effect == 261:
            if defender.hp < defender.starting_hp:
                power = 50 + (50 * (defender.starting_hp - defender.hp) // defender.starting_hp)
            else:
                power = 50

        if self.effect == 87:
            if attacker.hp <= attacker.starting_hp // 3:
                power = 200
            else:
                power = 50

        if self.effect == 264:
            power = 50 + (50 * (attacker.starting_hp - attacker.hp) // attacker.starting_hp)

        if self.effect == 266:
            power = 50 + (50 * (attacker.starting_hp - attacker.hp) // attacker.starting_hp)

        if self.effect == 45:
            power = 100 + (50 * (defender.starting_hp - defender.hp) // defender.starting_hp)

        if self.effect == 322:
            power = 60 * (2 ** (attacker.attack_stage))

        if self.effect == 323:
            power = 60 * (2 ** (attacker.spatk_stage))

        if self.effect == 324:
            power = 60 * (2 ** (attacker.speed_stage))

        if self.effect == 331:
            power = 60 * (2 ** (attacker.defense_stage))

        if self.effect == 332:
            power = 60 * (2 ** (attacker.spdef_stage))

        if self.effect == 326:
            power = 20 + (20 * attacker.attack_stage)
            if power < 1:
                power = 1

        if self.effect == 327:
            power = 20 + (20 * attacker.spatk_stage)
            if power < 1:
                power = 1

        if self.effect == 328:
            power = 20 + (20 * attacker.speed_stage)
            if power < 1:
                power = 1

        if self.effect == 362:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 363:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 364:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 365:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 366:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 371:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 372:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 373:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 374:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 375:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 376:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 377:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 378:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 379:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 380:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 381:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 382:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 383:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 384:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 385:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 386:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 387:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 388:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 389:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 390:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 391:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 392:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 393:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 394:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 395:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 396:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 397:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 398:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 399:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 400:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 401:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 402:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 403:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 404:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 405:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 406:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 407:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 408:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 409:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 410:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 411:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 412:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 413:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 414:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 415:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 416:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 417:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 418:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 419:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 420:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 421:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 422:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 423:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 424:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 425:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 426:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 427:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 428:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 429:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 430:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 431:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 432:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 433:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 434:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 435:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 436:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 437:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 438:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 439:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 440:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 441:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 442:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 443:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 444:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 445:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 446:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 447:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 448:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 449:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.effect == 450:
            power = 60 + (60 * attacker.positive_stat_count())

        if self.id == 573 and attacker.ability() == Ability.ORDINARY:
            power = attacker.level

        return power