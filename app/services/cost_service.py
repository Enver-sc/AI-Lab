def estimate_cost(input_tokens, output_tokens, model):
    return round(input_tokens / 1_000_000 * model.get("input_cost", 0) + output_tokens / 1_000_000 * model.get("output_cost", 0), 6)

def estimate_electricity_cost(energy_kwh, price_eur_per_kwh):
    # Unabhaengig vom Anbieterpreis: bildet ab, was der geschaetzte Stromverbrauch selbst kosten
    # wuerde -- bei lokalen Modellen ist "Kosten" (Anbieterpreis) sonst immer 0, obwohl echter
    # Strom verbraucht wird.
    return round(energy_kwh * price_eur_per_kwh, 6)

