import asyncio
from data.footballers import get_footballer_by_id
from config import MAX_CLUBS_TOTAL

def is_game_over(footballer, clubs_shown):
    total = len(footballer["clubs"])
    limit = min(MAX_CLUBS_TOTAL, total)
    print(f"clubs_shown={clubs_shown}, total={total}, limit={limit}, game_over={clubs_shown >= limit}")
    return clubs_shown >= limit

# Тест на Дрогба (id=49, у него 8 клубов)
f = get_footballer_by_id(49)
print(f"Футболист: {f['name']}, клубов: {len(f['clubs'])}")
print(f"MAX_CLUBS_TOTAL = {MAX_CLUBS_TOTAL}")
print("---")
for i in range(1, 10):
    is_game_over(f, i)
