from enum import Enum
from rlcard.games.limitholdem import PlayerStatus

class Action(Enum):
    FOLD = 0
    CHECK = 1
    CALL = 2
    RAISE_QUARTER_POT = 3
    RAISE_HALF_POT = 4
    RAISE_THREE_QUARTER_POT = 5
    RAISE_POT = 6
    RAISE_MIN = 7
    ALL_IN = 8

class NolimitholdemRound:
    def __init__(self, num_players, init_raise_amount, dealer, np_random):
        self.np_random = np_random
        self.game_pointer = None
        self.num_players = num_players
        self.init_raise_amount = init_raise_amount
        self.dealer = dealer
        self.not_raise_num = 0
        self.not_playing_num = 0
        self.raised = [0 for _ in range(self.num_players)]

    def start_new_round(self, game_pointer, players, raised=None):
        self.game_pointer = game_pointer
        self.not_raise_num = 0
        self.not_playing_num = 0

        # Blinds enforcement
        if raised:
            self.raised = raised
        else:
            self.raised = [0 for _ in range(self.num_players)]
            # --- Enforce blinds ---
            sb_pos = getattr(self.dealer, 'small_blind_pos', 0)
            bb_pos = getattr(self.dealer, 'big_blind_pos', 1)
            sb_amt = getattr(self.dealer, 'small_blind', 1)
            bb_amt = getattr(self.dealer, 'big_blind', 2)

            # Post small blind
            self.raised[sb_pos] = sb_amt
            players[sb_pos].bet(chips=sb_amt)
            # Post big blind
            self.raised[bb_pos] = bb_amt
            players[bb_pos].bet(chips=bb_amt)

    def proceed_round(self, players, action):
        #print("Proceed round: ", action)
        player = players[self.game_pointer]
        diff = max(self.raised) - self.raised[self.game_pointer]
        action = Action(action)
        
        if action == Action.CHECK:
            #print("CHECK")
            self.not_raise_num += 1

        elif action == Action.CALL:
            #print("CALL")
            call_amount = min(diff, player.remained_chips)
            self.raised[self.game_pointer] += call_amount
            player.bet(chips=call_amount)
            #self.dealer.pot += call_amount
            self.not_raise_num += 1

        elif action == Action.ALL_IN:
            #print("ALL_IN")
            all_in_quantity = player.remained_chips
            self.raised[self.game_pointer] += all_in_quantity
            player.bet(chips=all_in_quantity)
            #self.dealer.pot += all_in_quantity
            self.not_raise_num = 1

        elif action == Action.RAISE_POT:
            #print("RAISE_POT")
            raise_amt = min(self.dealer.pot, player.remained_chips)
            self.raised[self.game_pointer] += raise_amt
            player.bet(chips=raise_amt)
            #self.dealer.pot += raise_amt
            self.not_raise_num = 1

        elif action == Action.RAISE_THREE_QUARTER_POT:
            #print("RAISE_THREE_QUARTER_POT")
            raise_amt = min(int(self.dealer.pot * 0.75), player.remained_chips)
            self.raised[self.game_pointer] += raise_amt
            player.bet(chips=raise_amt)
            #self.dealer.pot += raise_amt
            self.not_raise_num = 1

        elif action == Action.RAISE_HALF_POT:
            #print("RAISE_HALF_POT")
            raise_amt = min(int(self.dealer.pot / 2), player.remained_chips)
            self.raised[self.game_pointer] += raise_amt
            player.bet(chips=raise_amt)
            #self.dealer.pot += raise_amt
            self.not_raise_num = 1

        elif action == Action.RAISE_QUARTER_POT:
            #print("RAISE_QUARTER_POT")
            raise_amt = min(int(self.dealer.pot / 4), player.remained_chips)
            self.raised[self.game_pointer] += raise_amt
            player.bet(chips=raise_amt)
            #self.dealer.pot += raise_amt
            self.not_raise_num = 1

        elif action == Action.RAISE_MIN:
            #print("RAISE_MIN")
            min_raise_amt = max(self.init_raise_amount, max(self.raised) - min(self.raised))
            raise_amt = min(min_raise_amt, player.remained_chips)
            self.raised[self.game_pointer] += raise_amt
            player.bet(chips=raise_amt)
            #self.dealer.pot += raise_amt
            self.not_raise_num = 1

        elif action == Action.FOLD:
            #print("FOLD")
            player.status = PlayerStatus.FOLDED
            self.not_playing_num += 1

        if player.remained_chips == 0 and player.status != PlayerStatus.FOLDED:
            player.status = PlayerStatus.ALLIN

        self.game_pointer = (self.game_pointer + 1) % self.num_players

        while players[self.game_pointer].status == PlayerStatus.FOLDED:
            self.game_pointer = (self.game_pointer + 1) % self.num_players

        return self.game_pointer

    def get_nolimit_legal_actions(self, players):
        player = players[self.game_pointer]
        diff = max(self.raised) - self.raised[self.game_pointer]
        actions = [Action.FOLD]
        if diff == 0:
            actions.append(Action.CHECK)
            # Only allow raising actions if player has chips and round is not over
            if player.remained_chips > 0:
                if player.remained_chips >= int(self.dealer.pot / 4):
                    actions.append(Action.RAISE_QUARTER_POT)
                if player.remained_chips >= int(self.dealer.pot / 2):
                    actions.append(Action.RAISE_HALF_POT)
                if player.remained_chips >= int(self.dealer.pot * 0.75):
                    actions.append(Action.RAISE_THREE_QUARTER_POT)
                if player.remained_chips >= int(self.dealer.pot):
                    actions.append(Action.RAISE_POT)
                if player.remained_chips >= max(self.init_raise_amount, max(self.raised) - min(self.raised)):
                    actions.append(Action.RAISE_MIN)
                actions.append(Action.ALL_IN)
        else:
            actions.append(Action.CALL)
            # Allow raising actions if player can cover
            if player.remained_chips > diff:
                if player.remained_chips >= diff + int(self.dealer.pot / 4):
                    actions.append(Action.RAISE_QUARTER_POT)
                if player.remained_chips >= diff + int(self.dealer.pot / 2):
                    actions.append(Action.RAISE_HALF_POT)
                if player.remained_chips >= diff + int(self.dealer.pot * 0.75):
                    actions.append(Action.RAISE_THREE_QUARTER_POT)
                if player.remained_chips >= diff + int(self.dealer.pot):
                    actions.append(Action.RAISE_POT)
                if player.remained_chips >= diff + max(self.init_raise_amount, max(self.raised) - min(self.raised)):
                    actions.append(Action.RAISE_MIN)
                actions.append(Action.ALL_IN)
        # Remove duplicates and preserve order
        seen = set()
        legal = []
        for a in actions:
            if a not in seen:
                legal.append(a)
                seen.add(a)
        return [a.value for a in legal]

    def is_over(self):
        # A round is over when all but one player have folded, or all active players are all-in, or all players have called
        if self.not_raise_num + self.not_playing_num >= self.num_players:
            return True
        return False
