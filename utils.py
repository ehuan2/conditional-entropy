import math


def entropy(P):
    ent = 0
    if type(P) is dict:
        for x in P:
            ent -= P[x] * math.log(P[x]) / math.log(2.0)
    elif type(P) is list:
        for x in P:
            ent -= x * math.log(x) / math.log(2.0)
    return ent
