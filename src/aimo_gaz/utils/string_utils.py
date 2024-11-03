
def parse_float(input):
    try:
        return float(input)
    except:
        pass
    try:
        return eval(input)
    except:
        pass
    return None
