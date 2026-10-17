from classifier import classify_score

def test_familiar_score():
    assert classify_score(1.0) == "FAMILIAR"
