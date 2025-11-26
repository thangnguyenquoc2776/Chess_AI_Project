import chess
import torch
import random
import os
from ai.agent_base import Agent
from .model import ChessTransformer
from .utils import ChessVocabulary

class TransformerAgent(Agent):
    name = "TransformerAI"

    def __init__(self, model_path="models/transformer_chess.pth", vocab_path="models/vocab.pkl"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_ready = False
        
        if os.path.exists(model_path) and os.path.exists(vocab_path):
            try:
                self.vocab = ChessVocabulary.load(vocab_path)
                self.model = ChessTransformer(vocab_size=self.vocab.vocab_size)
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.to(self.device)
                self.model.eval() 
                self.is_ready = True
                print("TransformerAgent: Đã load model thành công!")
            except Exception as e:
                print(f"TransformerAgent Error: {e}")
        else:
            print("TransformerAgent: Chưa tìm thấy file model. Sẽ đánh ngẫu nhiên.")

    def choose_move(self, board: chess.Board):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None, {} 

        if not self.is_ready:
            return random.choice(legal_moves), {"type": "random_fallback"}

        history = [m.uci() for m in board.move_stack]
        
        input_tensor, padding_mask = self.vocab.moves_to_tensor(history, self.device)
        
        with torch.no_grad():
            logits = self.model(input_tensor, src_key_padding_mask=padding_mask)
            probs = torch.softmax(logits, dim=1).squeeze(0) 

        sorted_indices = torch.argsort(probs, descending=True)
        
        best_move = None
        
        for idx in sorted_indices:
            move_uci = self.vocab.decode(idx.item())
            
            try:
                move_obj = chess.Move.from_uci(move_uci)
                if move_obj in legal_moves:
                    best_move = move_obj
                    break # Tìm thấy rồi!
            except:
                continue
        
        if best_move is None:
            best_move = random.choice(legal_moves)

        return best_move, {"type": "transformer", "prob": probs[self.vocab.encode(best_move.uci())].item()}