import maniphono
import hashlib

def digest(val):
    return hashlib.md5(str(val).encode("utf-8")).hexdigest()

def a():
    snd1 = maniphono.Sound("a")
    snd2 = maniphono.Sound("e")
    print(snd1, snd2)

    _, vector_a = maniphono.model_mipa.fvalue_vector(snd1.fvalues)
    _, vector_b = maniphono.model_mipa.fvalue_vector(snd2.fvalues)
    print("T", type(vector_a), type(vector_b))

    print(snd1, digest(vector_a))
    print(snd2, digest(vector_b))

def b():
    R = maniphono.DistanceRegressor()

    dist0 = R.distance("a", "a")
    print(dist0)
    dist1 = R.distance("a", "e")
    print(dist1)
    dist2 = R.distance("a", "cː")  # not in the model
    print(dist2)
    dist3 = R.distance("a", "ʒ")
    print(dist3)

b()