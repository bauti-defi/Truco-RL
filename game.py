
import numbers
import numpy as np
from envido import Envido
from actions import game_actions, envido_actions, truco_actions, response_actions, playable_cards
from truco import Truco
from card_game import CardGame

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class TrucoGame:
    
    
    def __init__(self, players, goes_first=0):
        '''
        Initialize a Game of Truco.
        '''
        self.players = players
        self.finished = False
        self.round = 0
        self.scoreboard = np.array([(p, 0) for p in players])
        self.first_move_by = self.players[goes_first] 
        self.second_move_by = self.players[1 - goes_first] 
        self.envido = Envido(self)
        self.truco = Truco(self)
        self.card_game = CardGame(self, self.first_move_by)

    def get_state(self):
        state = np.array()
        
        cards = []
        for player in self.players:
            cards = cards + player.hand

    
    def get_cards_played(self):
        return self.card_game.cards_played

    def update_score(self, player, score):
        if player == self.scoreboard[0][0]:
            self.scoreboard[0][1] += score
        else:
            self.scoreboard[1][1] += score
        
    def get_opponent(self, player):
        if player == self.players[0]:
            return self.players[1]
        else:
            return self.players[0]
    
    def get_mano(self):
        return self.card_game.card_next
        
    def finish_hand(self):
        self.finished = True
        logging.info("Hand finished.")
        logging.info(f"{self.scoreboard[0][0]} scored {self.scoreboard[0][1]}")
        logging.info(f"{self.scoreboard[1][0]} scored {self.scoreboard[1][1]}")
    
    def finish_round(self):
        self.round += 1
        
        first_played = self.card_game.cards_played[-2]
        second_played = self.card_game.cards_played[-1]
        comparison = first_played[1].tier - second_played[1].tier
        if comparison >= 0:
            self.card_game.switch_card_turn() # switch if second person wins round
            logging.debug(f"{second_played[0]} won the round. They will start the next one.")
        
        winner = self.card_game.get_card_winner()
        if winner is not None: 
            if self.truco.is_truco_started():
                reward = self.truco.get_truco_reward()
                self.update_score(winner, reward)
                logging.debug(f"{winner} was rewarded {reward} for winning truco.")
            else:
                self.update_score(winner, 1)
                logging.debug(f"{winner} was rewarded 1 for winning hand.")
            self.finish_hand()
        else:
            logging.debug("Round finished")
        
    def take_action(self, player, action):
        action_played = game_actions[action] if isinstance(action, numbers.Number) else action
        
        if action_played in envido_actions:
            if self.round == 0:
                if not self.truco.is_truco_active():
                    self.envido.take_action(player, action_played) 
                else:
                    logging.warn(f"{player}: Envido can only be played before Truco.")
            else:
                logging.warning(f"{player}: Envido can only be played in the first round")
        elif action_played in truco_actions:
            if not self.envido.is_envido_active():
                self.truco.take_action(player, action_played)
            else:
                logging.warning(f"{player} can't call {action_played} unless envido has finished.")
        elif action_played in response_actions:
            if self.envido.is_envido_active() and self.envido.is_valid_envido_state(action_played):
                if self.envido.envido_next == player:
                    self.envido.take_terminal_action(player, action_played) 
                else:
                    logging.warning(f"{player} can't call {action_played} envido for others.")
            elif self.truco.is_truco_active() and self.truco.is_valid_truco_state(action_played):
                self.truco.take_terminal_action(player, action_played)
            else:
                logging.warning(f"{player} can't call {action_played} right now.")
        elif action_played in playable_cards:
            if not self.envido.is_envido_active():
                if not self.truco.is_truco_active():
                    self.card_game.take_action(player, action_played)
                else:
                    logging.warning(f"{player} can't play the card {action_played} before responding to truco.")
            else:
                logging.warning(f"{player} can't play the card {action_played} before responding to envido.")
        elif action_played == "fold":
            logging.info(f"{player} folded.")
            if self.envido.is_envido_active():
               self.envido.fold(player)
            if self.truco.is_truco_started():
                self.truco.fold(player)
            else:
                opponent = self.get_opponent(player)
                self.update_score(opponent, 1)
                logging.debug(f"{opponent} was rewarded 1 for winning hand.")
            self.finish_hand()

        state = None

        return state
            
        
            
    