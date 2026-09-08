def normalize(value, unit):
    if unit != "celsius":
        raise ValueError("unsupported unit")
    return {"temperature_c": value}
