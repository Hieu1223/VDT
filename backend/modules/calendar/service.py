from common.business_calendar import get_business_calendar, update_business_calendar


async def get_calendar() -> dict:
    return await get_business_calendar()


async def update_calendar(payload: dict) -> dict:
    return await update_business_calendar(payload)
