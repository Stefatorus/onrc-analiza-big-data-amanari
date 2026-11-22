"""Step 5b: manual labels for the seeded 100-entry sample (05_manual_sample.py, SEED 20261122), keyed ONLY by sample position.
Labelled by the reviewer (AI model, see README annex) from the de-identified text alone, BEFORE any prediction was joined.
Rule used while labelling: the category is the document/issue the registrar asks to fix (e.g. a declaration of authorisation signed by the
wrong person -> CAEN; a declaration signed with an invalid signature -> SEMN); identity data of shareholders/administrators written in
the articles -> ASOC_ID; the registrar's standard closing text is ignored."""
MANUAL = {
    1: 'CAPITAL ACT CERERE', 2: 'SOLICITANT', 3: 'SOLICITANT', 4: 'CAEN', 5: 'ASOC_ID CERERE CAPITAL', 6: 'SEDIU', 7: 'CERERE',
    8: 'SOLICITANT', 9: 'SEMN', 10: 'CAEN', 11: 'ASOC_ID', 12: 'ACT CAEN SEDIU SEMN', 13: 'CAPITAL', 14: 'ACT', 15: 'SOLICITANT CAEN ACT',
    16: 'BEN_REAL', 17: 'CAPITAL', 18: 'CAEN', 19: 'CAEN', 20: 'ASOC_ID', 21: 'CERERE', 22: 'ACT', 23: 'CAEN ACT', 24: 'CAPITAL',
    25: 'CAEN', 26: 'SOLICITANT', 27: 'SEDIU ASOC_ID', 28: 'CAEN', 29: 'SEDIU', 30: 'SEDIU ASOC_ID CAPITAL', 31: 'CAEN BEN_REAL',
    32: 'ACT ASOC_ID', 33: 'SEDIU', 34: 'CAPITAL', 35: 'CAPITAL ASOC_ID', 36: 'SEDIU ASOC_ID', 37: 'ASOC_ID', 38: 'SOLICITANT SEMN INSTIT',
    39: 'SOLICITANT', 40: 'ASOC_ID CERERE', 41: 'ASOC_ID ACT', 42: 'INSTIT', 43: 'CAEN TARIF ACT', 44: 'ASOC_ID BEN_REAL', 45: 'SEMN',
    46: 'INSTIT', 47: 'SOLICITANT', 48: 'ASOC_ID', 49: 'CAEN', 50: 'CAEN ACT', 51: 'CAEN', 52: 'CAEN', 53: 'ACT ASOC_ID CAPITAL CAEN',
    54: 'ACT CAPITAL', 55: 'ACT', 56: 'INSTIT', 57: 'CAEN INSTIT', 58: 'SEDIU', 59: 'CERERE', 60: 'CAEN', 61: 'CAPITAL', 62: 'SEMN',
    63: 'CAEN', 64: 'CERERE', 65: 'SEDIU CAEN', 66: 'INSTIT', 67: 'CERERE', 68: 'ACT ASOC_ID TARIF CAPITAL', 69: 'SEDIU', 70: 'ACT ASOC_ID',
    71: 'SEDIU CAEN', 72: 'ACT', 73: 'SOLICITANT', 74: 'INSTIT', 75: 'CAPITAL', 76: 'CAEN', 77: 'ACT CAEN', 78: 'CAEN', 79: 'ASOC_ID INSTIT',
    80: 'INSTIT SEDIU', 81: 'CAEN', 82: 'CAEN', 83: 'SOLICITANT', 84: 'ACT', 85: 'CAEN', 86: 'CAEN', 87: 'INSTIT', 88: 'CAEN', 89: 'ACT',
    90: 'SEDIU', 91: 'CAEN', 92: 'CERERE ACT', 93: 'CAEN', 94: 'CERERE', 95: 'CERERE', 96: 'SEMN', 97: 'ASOC_ID SEDIU', 98: 'CERERE',
    99: 'ACT SOLICITANT', 100: 'CAEN INSTIT',
}
MANUAL = {k: frozenset(v.split()) for k, v in MANUAL.items()}
