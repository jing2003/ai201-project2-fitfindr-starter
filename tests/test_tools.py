import pytest

import tools
from tools import search_listings, suggest_outfit, create_fit_card


# ---------- Fake Groq client for LLM tool tests ----------

class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content):
        self.content = content

    def create(self, *args, **kwargs):
        return FakeResponse(self.content)


class FakeChat:
    def __init__(self, content):
        self.completions = FakeCompletions(content)


class FakeGroqClient:
    def __init__(self, content):
        self.chat = FakeChat(content)


@pytest.fixture
def sample_item():
    return {
        "id": "lst_006",
        "title": "Graphic Tee — 2003 Tour Bootleg Style",
        "description": "Vintage-style bootleg tee with faded graphic.",
        "category": "tops",
        "style_tags": ["graphic tee", "vintage", "grunge", "streetwear"],
        "size": "L",
        "condition": "good",
        "price": 24.00,
        "colors": ["black"],
        "brand": None,
        "platform": "depop",
    }


# ---------- search_listings tests ----------

def test_search_listings_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0


def test_search_listings_no_results_returns_empty_list():
    """
    Error handling match:
    search_listings failure mode = no results match the query.
    Expected tool behavior = return [] without raising an exception.
    """
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_listings_price_filter():
    results = search_listings("vintage", size=None, max_price=30)

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(item["price"] <= 30 for item in results)


def test_search_listings_size_filter():
    results = search_listings("graphic tee", size="M", max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0
    assert all("m" in item["size"].lower() for item in results)


# ---------- suggest_outfit tests ----------

def test_suggest_outfit_empty_wardrobe_returns_general_advice(monkeypatch, sample_item):
    """
    Error handling match:
    suggest_outfit failure mode = wardrobe is empty.
    Expected tool behavior = do not crash; return a non-empty general styling response.
    """
    fake_response = (
        "Since your wardrobe is empty, style this graphic tee with baggy jeans, "
        "chunky sneakers, and a flannel for a relaxed grunge streetwear look."
    )

    monkeypatch.setattr(
        tools,
        "_get_groq_client",
        lambda: FakeGroqClient(fake_response),
    )

    empty_wardrobe = {"items": []}

    result = suggest_outfit(sample_item, empty_wardrobe)

    assert isinstance(result, str)
    assert result.strip() != ""
    assert "graphic tee" in result.lower() or "tee" in result.lower()


def test_suggest_outfit_missing_wardrobe_dict_still_returns_string(monkeypatch, sample_item):
    """
    Extra guard:
    If wardrobe is None instead of {"items": []}, the tool should still handle it gracefully.
    """
    fake_response = (
        "Try styling this tee with relaxed denim, sneakers, and a casual jacket "
        "for an easy thrifted streetwear outfit."
    )

    monkeypatch.setattr(
        tools,
        "_get_groq_client",
        lambda: FakeGroqClient(fake_response),
    )

    result = suggest_outfit(sample_item, None)

    assert isinstance(result, str)
    assert result.strip() != ""


def test_suggest_outfit_with_wardrobe_returns_named_pieces(monkeypatch, sample_item):
    fake_response = (
        "Wear the Graphic Tee — 2003 Tour Bootleg Style with Baggy straight-leg jeans "
        "and Chunky sneakers for a casual vintage streetwear outfit."
    )

    monkeypatch.setattr(
        tools,
        "_get_groq_client",
        lambda: FakeGroqClient(fake_response),
    )

    wardrobe = {
        "items": [
            {
                "id": "w_001",
                "name": "Baggy straight-leg jeans",
                "category": "bottoms",
                "colors": ["dark blue"],
                "style_tags": ["denim", "streetwear", "baggy"],
                "notes": "High-waisted",
            },
            {
                "id": "w_002",
                "name": "Chunky sneakers",
                "category": "shoes",
                "colors": ["white"],
                "style_tags": ["streetwear", "chunky"],
                "notes": "Good for casual outfits",
            },
        ]
    }

    result = suggest_outfit(sample_item, wardrobe)

    assert isinstance(result, str)
    assert result.strip() != ""
    assert "Baggy straight-leg jeans" in result
    assert "Chunky sneakers" in result


# ---------- create_fit_card tests ----------

def test_create_fit_card_empty_outfit_returns_error_message(monkeypatch, sample_item):
    """
    Error handling match:
    create_fit_card failure mode = outfit input is missing.
    Expected tool behavior = return a descriptive error message string and do not call the LLM.
    """
    def fake_client():
        raise AssertionError("LLM should not be called for empty outfit input")

    monkeypatch.setattr(tools, "_get_groq_client", fake_client)

    result = create_fit_card("", sample_item)

    assert isinstance(result, str)
    assert result.strip() != ""
    assert "cannot create" in result.lower() or "missing" in result.lower()


def test_create_fit_card_whitespace_outfit_returns_error_message(monkeypatch, sample_item):
    """
    Error handling match:
    create_fit_card failure mode = outfit input is only whitespace.
    Expected tool behavior = return a descriptive error message string and do not call the LLM.
    """
    def fake_client():
        raise AssertionError("LLM should not be called for whitespace outfit input")

    monkeypatch.setattr(tools, "_get_groq_client", fake_client)

    result = create_fit_card("   ", sample_item)

    assert isinstance(result, str)
    assert result.strip() != ""
    assert "cannot create" in result.lower() or "missing" in result.lower()


def test_create_fit_card_none_outfit_returns_error_message(monkeypatch, sample_item):
    """
    Extra guard:
    If outfit is None, the tool should still return an error string instead of crashing.
    """
    def fake_client():
        raise AssertionError("LLM should not be called for None outfit input")

    monkeypatch.setattr(tools, "_get_groq_client", fake_client)

    result = create_fit_card(None, sample_item)

    assert isinstance(result, str)
    assert result.strip() != ""
    assert "cannot create" in result.lower() or "missing" in result.lower()


def test_create_fit_card_valid_outfit_returns_caption(monkeypatch, sample_item):
    fake_caption = (
        "Found this Graphic Tee — 2003 Tour Bootleg Style on depop for $24, "
        "and it has the perfect faded streetwear vibe. I'd wear it with baggy jeans "
        "and chunky sneakers for an easy thrifted fit."
    )

    monkeypatch.setattr(
        tools,
        "_get_groq_client",
        lambda: FakeGroqClient(fake_caption),
    )

    outfit = (
        "Style the graphic tee with baggy jeans and chunky sneakers for a relaxed "
        "vintage streetwear look."
    )

    result = create_fit_card(outfit, sample_item)

    assert isinstance(result, str)
    assert result.strip() != ""
    assert "depop" in result.lower()
    assert "$24" in result
