from agent import run_agent
from utils.data_loader import get_example_wardrobe

print("=" * 70)
print("FITFINDR DEMO: COMPLETE MULTI-STEP INTERACTION")
print("=" * 70)

query = "looking for a vintage graphic tee under $30"
wardrobe = get_example_wardrobe()

print("\nSTEP 1: User query")
print(query)

print("\nSTEP 2: Agent calls run_agent(query, wardrobe)")
print("The planning loop will parse the query, search listings, suggest an outfit, and create a fit card.")

session = run_agent(query, wardrobe)

print("\nSTEP 3: Parsed search parameters stored in session['parsed']")
print(session["parsed"])

print("\nSTEP 4: search_listings() result stored in session['search_results']")
print("Number of listings found:", len(session["search_results"]))

print("\nSTEP 5: Top listing selected and stored in session['selected_item']")
print(session["selected_item"])

print("\nSTEP 6: session['selected_item'] is passed into suggest_outfit()")
print("Outfit suggestion stored in session['outfit_suggestion']:")
print(session["outfit_suggestion"])

print("\nSTEP 7: session['outfit_suggestion'] and session['selected_item'] are passed into create_fit_card()")
print("Fit card stored in session['fit_card']:")
print(session["fit_card"])

print("\nFINAL HAPPY PATH SESSION STATE:")
print("error:", session["error"])
print("selected_item is None:", session["selected_item"] is None)
print("outfit_suggestion is None:", session["outfit_suggestion"] is None)
print("fit_card is None:", session["fit_card"] is None)

print("\n" + "=" * 70)
print("FITFINDR DEMO: TRIGGERED FAILURE MODE")
print("=" * 70)

bad_query = "designer ballgown size XXS under $5"

print("\nSTEP 1: User enters an impossible query")
print(bad_query)

print("\nSTEP 2: Agent calls search_listings(), which returns no matches")
failure_session = run_agent(bad_query, wardrobe)

print("\nSTEP 3: Agent stores a helpful error in session['error']")
print("error:", failure_session["error"])

print("\nSTEP 4: Agent stops early and does not create outfit or fit card")
print("selected_item:", failure_session["selected_item"])
print("outfit_suggestion:", failure_session["outfit_suggestion"])
print("fit_card:", failure_session["fit_card"])

print("\nFINAL FAILURE SESSION STATE:")
print(failure_session)
