from typing import Optional

from database.db import apply_referral

REFERRAL_BONUS = 1500


def parse_ref_id(start_param: Optional[str]) -> Optional[int]:
    if not start_param or not start_param.startswith("ref_"):
        return None
    try:
        return int(start_param[4:])
    except ValueError:
        return None


async def apply_start_param(user_id: int, start_param: Optional[str], bot=None) -> bool:
    """Applies the referral bonus if start_param is a ref_<id> link. apply_referral()
    itself guards against self-referral and re-application to an already-referred user.
    Returns True if the bonus was applied. Optionally notifies the referrer via `bot`."""
    ref_id = parse_ref_id(start_param)
    if not ref_id:
        return False

    bonus_given = await apply_referral(user_id, ref_id)
    if bonus_given and bot is not None:
        try:
            await bot.send_message(
                ref_id,
                f"🎉 По твоей ссылке зарегистрировался новый игрок!\n\n"
                f"💰 *+{REFERRAL_BONUS} очков* начислено на твой счёт! 🔥",
                parse_mode="Markdown",
            )
        except Exception:
            pass
    return bonus_given
