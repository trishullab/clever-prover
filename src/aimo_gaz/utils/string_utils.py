
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

def history_to_str(history):
    if len(history) > 10:
        return "[...,\n{}]".format(",\n".join(map(str, history[-10:])))
    else:
        return "[{}]".format(",\n".join(map(str, history)))
