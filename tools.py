"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)

def _call_groq_chat(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 350,
    model: str = "llama-3.3-70b-versatile",
) -> str:
    """
    Shared helper for LLM-powered tools.
    Returns an empty string if the model response is missing.
    """
    client = _get_groq_client()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if not response.choices:
        return ""

    content = response.choices[0].message.content

    if not content:
        return ""

    return content.strip()

# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase and trim text safely."""
    return str(text or "").strip().lower()

def _tokenize(text: str) -> set[str]:
    """Turn text into lowercase word tokens."""
    return set(re.findall(r"[a-z0-9]+", _normalize(text)))

def _size_matches(listing_size: str, requested_size: str) -> bool:
    """
    Case-insensitive size matching.
    Example: requested 'M' matches listing size 'S/M'.
    """
    listing_size_tokens = _tokenize(listing_size)
    requested_size_tokens = _tokenize(requested_size)

    if not listing_size_tokens or not requested_size_tokens:
        return False

    return any(token in listing_size_tokens for token in requested_size_tokens)

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
    query_tokens = _tokenize(description)

    if not query_tokens:
        return []

    scored_results: list[tuple[int, dict]] = []

    for listing in listings:
        if max_price is not None and listing.get("price", float("inf")) > max_price:
            continue

        if size is not None and not _size_matches(listing.get("size", ""), size):
            continue

        searchable_text = " ".join(
            [
                str(listing.get("title", "")),
                str(listing.get("description", "")),
                str(listing.get("category", "")),
                " ".join(listing.get("style_tags", [])),
                str(listing.get("size", "")),
                str(listing.get("condition", "")),
                " ".join(listing.get("colors", [])),
                str(listing.get("brand") or ""),
                str(listing.get("platform", "")),
            ]
        )

        listing_tokens = _tokenize(searchable_text)
        score = len(query_tokens.intersection(listing_tokens))

        if score == 0:
            continue

        scored_results.append((score, listing))

    scored_results.sort(key=lambda result: result[0], reverse=True)

    return [listing for score, listing in scored_results]

# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _format_new_item(new_item: dict) -> str:
    """Format a listing dict into readable text for the LLM."""
    return f"""
        Title: {new_item.get("title", "Unknown item")}
        Description: {new_item.get("description", "No description provided")}
        Category: {new_item.get("category", "Unknown")}
        Style tags: {", ".join(new_item.get("style_tags", []))}
        Size: {new_item.get("size", "Unknown")}
        Condition: {new_item.get("condition", "Unknown")}
        Price: {f"${new_item['price']:.2f}" if isinstance(new_item.get("price"), (int, float)) else "Unknown"}
        Colors: {", ".join(new_item.get("colors", []))}
        Brand: {new_item.get("brand") or "Unknown"}
        Platform: {new_item.get("platform", "Unknown")}
    """.strip()

def _format_wardrobe_items(items: list[dict]) -> str:
    """Format wardrobe items into readable text for the LLM."""
    formatted_items = []

    for item in items:
        formatted_items.append(
            f"""
                - {item.get("name", "Unnamed item")}
                Category: {item.get("category", "Unknown")}
                Colors: {", ".join(item.get("colors", []))}
                Style tags: {", ".join(item.get("style_tags", []))}
                Notes: {item.get("notes", "None")}
            """.strip()
        )

    return "\n\n".join(formatted_items)

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    item_text = _format_new_item(new_item)

    if not wardrobe_items:
        prompt = f"""
            The user is considering buying this thrifted item:

            {item_text}

            The user's wardrobe is empty or not provided.

            Suggest 1–2 complete outfit ideas using this item. Since there are no saved wardrobe pieces,
            give general styling advice instead of mentioning specific closet items.

            Include:
            - What clothing pieces would pair well with it
            - What shoes or accessories could work
            - The overall vibe of the outfit

            Keep the response casual, helpful, and concise.
        """.strip()
    else:
        wardrobe_text = _format_wardrobe_items(wardrobe_items)

        prompt = f"""
            The user is considering buying this thrifted item:

            {item_text}

            The user's wardrobe contains these items:

            {wardrobe_text}

            Suggest 1–2 complete outfits using the thrifted item and specific named pieces from the user's wardrobe.

            Rules:
            - Mention the thrifted item by name.
            - Use named wardrobe pieces when possible.
            - If the wardrobe does not have enough matching pieces, say what is missing and suggest general alternatives.
            - Keep the response casual, helpful, and concise.
        """.strip()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful fashion styling assistant for a thrift shopping app. "
                "You suggest realistic, wearable outfits based only on the item and wardrobe information provided."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:
        outfit = _call_groq_chat(
            messages=messages,
            temperature=0.7,
            max_tokens=450,
        )

        if outfit:
            return outfit

        return (
            "I could not generate a specific outfit suggestion, but this item could be styled "
            "with simple basics, matching shoes, and accessories that fit its color and overall vibe."
        )

    except Exception as e:
        return f"Could not generate outfit suggestions because the LLM call failed: {e}"


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def _format_item_for_caption(new_item: dict) -> str:
    """Format available item details without inventing missing values."""
    lines = []

    if new_item.get("title"):
        lines.append(f"Item name: {new_item['title']}")

    if new_item.get("price") is not None:
        price = new_item["price"]
        if isinstance(price, (int, float)):
            lines.append(f"Price: ${price:.2f}")
        else:
            lines.append(f"Price: {price}")

    if new_item.get("platform"):
        lines.append(f"Platform: {new_item['platform']}")

    if new_item.get("description"):
        lines.append(f"Description: {new_item['description']}")

    if new_item.get("category"):
        lines.append(f"Category: {new_item['category']}")

    if new_item.get("style_tags"):
        lines.append(f"Style tags: {', '.join(new_item['style_tags'])}")

    if new_item.get("colors"):
        lines.append(f"Colors: {', '.join(new_item['colors'])}")

    if new_item.get("brand"):
        lines.append(f"Brand: {new_item['brand']}")

    if new_item.get("condition"):
        lines.append(f"Condition: {new_item['condition']}")

    return "\n".join(lines)

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if outfit is None or not str(outfit).strip():
        return (
            "Cannot create a fit card because the outfit suggestion is missing "
            "or empty."
        )

    item_text = _format_item_for_caption(new_item)

    prompt = f"""
        Create a short, shareable outfit caption for a thrifted fashion find.

        Item details:
        {item_text}

        Outfit suggestion:
        {str(outfit).strip()}

        Caption requirements:
        - Write 2–4 sentences.
        - Make it sound casual and authentic, like a real Instagram or TikTok OOTD post.
        - Mention the item name naturally once if it is provided.
        - Mention the price naturally once if it is provided.
        - Mention the platform naturally once if it is provided.
        - Capture the outfit vibe in specific terms.
        - Do not sound like a product description.
        - Do not invent missing details.
        - Do not use hashtags unless they feel natural.
    """.strip()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a casual fashion caption writer for a thrift styling app. "
                "Write authentic, varied, social-media-ready outfit captions."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:
        caption = _call_groq_chat(
            messages=messages,
            temperature=1.0,
            max_tokens=220,
        )

        if caption:
            return caption

        return "Could not create a fit card because the LLM returned an empty caption."

    except Exception as e:
        return f"Could not create a fit card because the LLM call failed: {e}"
