import torch
from game import TrucoGame
import logging
import random
from actions import game_actions


logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

def encode_game_state(player, game):
    state = game.get_state(player)

    game_t = torch.tensor(state['game']).reshape(-1).squeeze()
    score_t = torch.tensor(state['score']).reshape(-1).squeeze()
    player_cards_t = torch.tensor(state['player_cards']).reshape(-1).squeeze()
    cards_played_t = torch.tensor(state['cards_played']).reshape(-1).squeeze()
    envido_state_t = torch.cat((torch.tensor(state['envido_state'][0]).reshape(-1).squeeze(), torch.tensor(state['envido_state'][1])))
    truco_state_t = torch.tensor(state['truco_state']).reshape(-1).squeeze()

    return torch.cat((game_t, score_t, player_cards_t, cards_played_t, envido_state_t, truco_state_t)).type(torch.FloatTensor)

class TrucoEnvironment:

    def __init__(self, players):
        self.game = TrucoGame(players)
        self.action_space_dim=game_actions.shape[0]
        self.state_space_dim=encode_game_state(self.game.get_mano(), self.game).shape[0]
        self.players = players
        self.games_won = [(p, 0) for p in players]
        self.games_played = 0

    def reset(self): 
        logging.info("New Game.")
        # Clear player cards
        for player in self.players:
            player.hand.clear()
            
        winner = self.game.get_winner()
        if winner is not None:
            self.games_won = [(p, wins + 1) if p == winner else (p, wins) for p, wins in self.games_won]
            self.games_played = self.games_won[0][1] + self.games_won[1][1]
        else:
            logging.warn("Game ended with no winner.")
            
        self.game = TrucoGame(self.players, goes_first=random.getrandbits(1))
        
        first_move_by = self.game.get_mano()
        
        return first_move_by, self.game.get_legal_actions(first_move_by), encode_game_state(first_move_by, self.game)

    def step(self, player, action):
        old_score = self.game.scoreboard.copy()
        
        self.game.take_action(player, action)
        next_player = self.game.get_mano()
        
        new_score = self.game.scoreboard.copy()
        reward = 0
        for i in range(len(new_score)):
            if new_score[i][0] == player:
                reward += (new_score[i][1] - old_score[i][1])
            else:
                reward -= (new_score[i][1] - old_score[i][1])
        
        return reward, 1 if self.game.finished else 0, next_player, self.game.get_legal_actions(next_player), encode_game_state(next_player, self.game)
        