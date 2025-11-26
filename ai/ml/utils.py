# ai/ml/utils.py
import joblib
import torch
from typing import List, Dict, Optional, Tuple

class ChessVocabulary:
    """Quản lý việc ánh xạ nước đi UCI (str) <-> Index (int)."""
    def __init__(self, moves: Optional[List[str]] = None, max_len: int = 80):
        self.max_len = max_len 
        
        self.PAD_TOKEN = '<pad>' 
        self.SOS_TOKEN = '<sos>' 
        self.UNK_TOKEN = '<unk>' 
        
        self.stoi: Dict[str, int] = {
            self.PAD_TOKEN: 0,
            self.SOS_TOKEN: 1,
            self.UNK_TOKEN: 2,
        }
        self.itos: Dict[int, str] = {v: k for k, v in self.stoi.items()}
        
        if moves:
            for i, move in enumerate(moves):
                idx = i + 3 
                self.stoi[move] = idx
                self.itos[idx] = move
        
        self.vocab_size = len(self.stoi)

    @classmethod
    def load(cls, path: str):
        return joblib.load(path)

    def save(self, path: str):
        joblib.dump(self, path)
        
    def encode(self, uci_move: str) -> int:
        return self.stoi.get(uci_move, self.stoi[self.UNK_TOKEN])

    def decode(self, index: int) -> str:
        return self.itos.get(index, self.UNK_TOKEN)

    def moves_to_tensor(self, move_history: List[str], device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        # CRITICAL FIX: Always start with <sos>
        sequence = [self.SOS_TOKEN] + move_history[-self.max_len + 1:]  # +1 because we added SOS
        
        encoded = [self.encode(move) for move in sequence]
        
        # Left-pad to max_len
        padding_needed = self.max_len - len(encoded)
        if padding_needed > 0:
            padded_encoded = [self.stoi[self.PAD_TOKEN]] * padding_needed + encoded
        else:
            padded_encoded = encoded[-self.max_len:]  # truncate old games if any

        input_tensor = torch.tensor([padded_encoded], dtype=torch.long, device=device)
        padding_mask = (input_tensor == self.stoi[self.PAD_TOKEN])
        
        return input_tensor, padding_mask