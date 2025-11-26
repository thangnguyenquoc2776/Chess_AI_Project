# ai/ml/model.py
import torch
import torch.nn as nn
import math

def get_sinusoidal_positional_encoding(max_seq_len: int, d_model: int, device=None):
    pe = torch.zeros(max_seq_len, d_model, device=device)
    position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
    div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
    pe[:, 0::2] = torch.sin(position * div_term)
    pe[:, 1::2] = torch.cos(position * div_term)
    return pe.unsqueeze(0)  # (1, seq_len, d_model)

class ChessTransformer(nn.Module):
    def __init__(self, vocab_size, d_model=256, nhead=8, num_layers=6, max_seq_len=80, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        
        # Sinusoidal PE (fixed, no learning needed)
        self.register_buffer(
            'pos_encoding', 
            get_sinusoidal_positional_encoding(max_seq_len, d_model)
        )
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dim_feedforward=1024, 
            dropout=dropout, 
            batch_first=True,
            activation='gelu'  # small bonus
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.dropout = nn.Dropout(dropout)
        self.fc_out = nn.Linear(d_model, vocab_size)
        
        # Weight initialization (helps a lot)
        self._init_weights()

    def _init_weights(self):
        initrange = 0.1
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.fc_out.bias.data.zero_()
        self.fc_out.weight.data.uniform_(-initrange, initrange)

    def forward(self, x, src_key_padding_mask=None):
        seq_len = x.size(1)
        
        x = self.embedding(x) * math.sqrt(self.d_model)
        
        # Add positional encoding (automatically broadcasts)
        x = x + self.pos_encoding[:, :seq_len, :]
        
        x = self.dropout(x)
        
        x = self.transformer_encoder(x, src_key_padding_mask=src_key_padding_mask)
        
        # Predict next move from the LAST token
        x = x[:, -1, :] 
        
        x = self.fc_out(x)
        return x