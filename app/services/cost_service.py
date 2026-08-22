def estimate_cost(input_tokens, output_tokens, model):
    return round(input_tokens / 1_000_000 * model.get("input_cost", 0) + output_tokens / 1_000_000 * model.get("output_cost", 0), 6)

