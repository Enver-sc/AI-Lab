def estimate_sustainability(input_tokens, output_tokens, model, carbon_intensity=350):
    energy = input_tokens / 1000 * model["input_energy"] + output_tokens / 1000 * model["output_energy"]
    return {"energy_kwh": round(energy, 6), "co2_grams": round(energy * carbon_intensity, 4)}

def estimate_duration(input_tokens, output_tokens, complexity, model):
    seconds = model["latency_ms"] / 1000 + input_tokens / 1800 + output_tokens / (70 if "cloud" in model["model_class"] else 35) + complexity / 120
    return {"min_seconds": round(max(.2, seconds * .75), 1), "max_seconds": round(seconds * 1.35, 1)}

