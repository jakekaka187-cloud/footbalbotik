from dataclasses import dataclass
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
    season_score: int = 0
    season_wins: int = 0
    referred_by: Optional[int] = None
    referral_count: int = 0
