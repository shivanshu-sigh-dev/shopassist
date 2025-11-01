import json

def is_strict_json_object(s: str) -> bool:
    """Return True if s is exactly a JSON object (dict) and nothing else."""
    
    if not isinstance(s, str):
        return False
    
    s_strip = s.replace("```json", '').replace("```", '').strip()
    if not s_strip:
        return False
    
    try:
        decoder = json.JSONDecoder()
        obj, idx = decoder.raw_decode(s_strip)  # parse from start
    except ValueError:
        return False
    
    return isinstance(obj, dict) and s_strip[idx:].strip() == ""

def compare_dicts(source: dict, target: dict) -> int:    
    matches = sum(1 for k in source if source[k] == target.get(k))
    return matches