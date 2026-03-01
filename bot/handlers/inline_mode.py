# bot/handlers/inline_mode.py
import hashlib
from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent
from database.manager import get_user_cards
from utils.cards import get_all_cards, get_card_by_code
from config import config

router = Router(name="inline_mode")

@router.inline_query()
async def inline_collection_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    query = inline_query.query.strip().lower()
    
    # Get user's cards
    user_codes = get_user_cards(user_id)
    if not user_codes:
        # Return a simple "no cards" message
        await inline_query.answer(
            results=[],
            switch_pm_text="Koleksiyangiz bo'sh. Kartalar yig'ishni boshlang!",
            switch_pm_parameter="start"
        )
        return

    all_cards = get_all_cards(include_disabled=True)
    owned_cards = [c for c in all_cards if c["code"] in user_codes]
    
    # Filter by query if provided
    if query:
        results_cards = [
            c for c in owned_cards 
            if query in c["name"].lower() or query in c["code"].lower()
        ]
    else:
        results_cards = owned_cards[:50] # Limit to 50 results

    results = []
    for card in results_cards:
        # Construct the display text
        text = (
            f"🎴 <b>{card['name']}</b> ({card['code']})\n"
            f"✨ Rarity: {card['rarity']}\n"
            f"👤 Owner: {inline_query.from_user.full_name}"
        )
        
        # Decide result type (Photo if image exists, else Article)
        # For simplicity in this demo, we'll use Article with a nice description
        # or Photo if we had direct URLs per card.
        
        result_id = hashlib.md5(f"{user_id}:{card['code']}".encode()).hexdigest()
        
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=f"{card['name']} [{card['code']}]",
                description=f"{card['rarity']} | {card['element'] if 'element' in card else ''}",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode="HTML"
                )
            )
        )

    await inline_query.answer(
        results=results,
        cache_time=5,
        is_personal=True
    )
