from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class User:
    telegram_id: int
    username: Optional[str]
    first_name: str
    games_played: int = 0
    games_won: int = 0
    games_lost: int = 0
    total_score: int = 0
    best_score: int = 0
    current_streak: int = 0
    best_streak: int = 0
    created_at: Optional[datetime] = None


@dataclass
class Footballer:
    id: int
    name: str
    clubs: list  # list of dicts: [{name, years, emoji}]
    nationality: str
    position: str
    difficulty: int  # 1-3 (easy/medium/hard)
    hint_text: Optional[str] = None  # additional hint if needed


@dataclass
class GameSession:
    session_id: str
    mode: str  # 'solo' or 'pvp'
    footballer_id: int
    clubs_shown: int = 0
    player1_id: Optional[int] = None
    player2_id: Optional[int] = None
    current_turn: Optional[int] = None  # telegram_id
    status: str = "waiting"  # waiting / active / finished
    winner_id: Optional[int] = None
    created_at: Optional[datetime] = None