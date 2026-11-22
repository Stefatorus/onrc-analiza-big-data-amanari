"""Step 5b: manual labels for the seeded 100-entry sample (05_manual_sample.py, SEED 20261122), keyed ONLY by sample position.
Labelled by the reviewer (AI model, see README annex) from the de-identified full reason text alone, right after step 2 and BEFORE
embeddings, clustering or any classifier had been run.

Layer B (substantive cause, multi-label). Rules used while labelling (same as delay_reasons/05 where the category exists there):
  * the category is the document/issue the registrar asks to fix; a declaration of authorisation signed by the wrong person -> CAEN;
    an invalid/missing signature -> SEMN; identity data of shareholders/administrators in the articles -> ASOC_ID;
  * the registration form (CERERE) is labelled only when the form itself is wrong (wrong request type, wrong item, missing page, unclear
    object of the request, parallel request), NOT when it is merely the vehicle of another correction ("se va reface cererea");
  * FARA_OBIECT = the request has no object (e.g. the CAEN Rev.3 update or the data were already registered);
  * IMPOSIBIL = legal impediment that documents cannot cure within the term (one-PFA rule of OUG 44/2008, dissolution time limits,
    pending opposition/litigation);
  * NERESTATAT = the rejection states only that the postponement was not complied with, without restating any cause;
  * the registrar's standard text (art. 77, art. 106(4)/(5), "se respinge") is ignored.
Layer A (procedural mechanism, single label): M_NEREMEDIAT / M_PARTIAL / M_AMANARE_ALT / M_DIRECT (definitions in 02_normalize_split.py).
"""
MANUAL = {
    1: 'CERERE', 2: 'CAEN INSTIT BEN_REAL SEDIU', 3: 'FARA_OBIECT', 4: 'CAEN', 5: 'CERERE', 6: 'ACT ASOC_ID', 7: 'FARA_OBIECT', 8: 'CAEN',
    9: 'CAPITAL', 10: 'CAEN IMPOSIBIL', 11: 'CAEN', 12: 'SOLICITANT', 13: 'TARIF ACT', 14: 'ACT', 15: 'CERERE', 16: 'SOLICITANT',
    17: 'FARA_OBIECT', 18: 'ACT ASOC_ID CAEN TARIF DENUM', 19: 'SEDIU CAEN', 20: 'INSTIT SEDIU CAEN ASOC_ID', 21: 'SEDIU SEMN',
    22: 'ASOC_ID', 23: 'ACT', 24: 'SOLICITANT', 25: 'ASOC_ID', 26: 'CAEN', 27: 'SEDIU ASOC_ID BEN_REAL', 28: 'FARA_OBIECT SOLICITANT',
    29: 'NERESTATAT', 30: 'SEDIU CAEN', 31: 'SOLICITANT SEMN', 32: 'SEDIU', 33: 'INSTIT CAEN SEDIU', 34: 'ACT TARIF CAEN',
    35: 'ACT SEDIU CAEN', 36: 'ASOC_ID ACT BEN_REAL CERERE', 37: 'BEN_REAL', 38: 'ASOC_ID', 39: 'SEDIU ASOC_ID', 40: 'FARA_OBIECT',
    41: 'CAEN', 42: 'SEMN CAEN BEN_REAL INSTIT', 43: 'CAEN', 44: 'NERESTATAT', 45: 'CAEN', 46: 'CAEN', 47: 'CAEN', 48: 'SEDIU',
    49: 'CERERE', 50: 'SEMN SEDIU', 51: 'SOLICITANT', 52: 'SEDIU SEMN', 53: 'SEDIU', 54: 'CAPITAL', 55: 'CAEN', 56: 'CAEN',
    57: 'INSTIT CAEN', 58: 'IMPOSIBIL CAPITAL', 59: 'CAEN', 60: 'NERESTATAT', 61: 'CERERE CAEN SEDIU', 62: 'CAEN', 63: 'SOLICITANT',
    64: 'INSTIT ASOC_ID', 65: 'INSTIT ASOC_ID', 66: 'CAEN', 67: 'CAEN INSTIT', 68: 'FARA_OBIECT', 69: 'ASOC_ID CAEN', 70: 'NERESTATAT',
    71: 'SEMN', 72: 'ASOC_ID CERERE SEDIU CAEN', 73: 'INSTIT', 74: 'SOLICITANT', 75: 'CERERE SEDIU', 76: 'SEDIU INSTIT', 77: 'ASOC_ID',
    78: 'SOLICITANT CERERE', 79: 'CAEN SEMN', 80: 'SEDIU', 81: 'CAPITAL', 82: 'SEDIU CAPITAL', 83: 'ACT BEN_REAL SOLICITANT',
    84: 'INSTIT CAEN SEMN', 85: 'SEDIU', 86: 'CAEN INSTIT', 87: 'CAEN', 88: 'CAEN', 89: 'SOLICITANT', 90: 'CAEN', 91: 'ACT', 92: 'DENUM',
    93: 'SOLICITANT', 94: 'CAPITAL INSTIT', 95: 'CAEN', 96: 'SOLICITANT INSTIT ACT', 97: 'CERERE SEDIU', 98: 'CAEN', 99: 'CERERE',
    100: 'IMPOSIBIL',
}
MANUAL = {k: frozenset(v.split()) - {'NERESTATAT'} for k, v in MANUAL.items()}   # NERESTATAT = empty set of substantive causes

_DIRECT = {3, 11, 13, 17, 22, 25, 28, 33, 48, 58, 63, 69, 85, 93, 99}
_PARTIAL = {10, 31, 32, 52, 57, 72}
_ALT = set()
MECH = {k: ('M_DIRECT' if k in _DIRECT else 'M_PARTIAL' if k in _PARTIAL else 'M_AMANARE_ALT' if k in _ALT else 'M_NEREMEDIAT') for k in range(1, 101)}

# ---- second, out-of-sample batch (05_manual_sample.sample_eids2, SEED2 20261123, 50 entries not in the first 100).
# Drawn and labelled AFTER the classifier (04) had been fixed and validated on batch 1, but BEFORE joining its predictions;
# it checks the rules (FARA_OBIECT, IMPOSIBIL, CERERE pre-cleaning) that were written after reading batch 1. Same labelling rules.
MANUAL2 = {
    1: 'CAEN', 2: 'ASOC_ID CERERE ACT', 3: 'CAEN SEDIU', 4: 'FARA_OBIECT', 5: 'SOLICITANT', 6: 'FARA_OBIECT', 7: 'INSTIT CAEN ACT',
    8: 'ASOC_ID', 9: 'SEDIU INSTIT', 10: 'CAEN', 11: 'SOLICITANT CAPITAL', 12: 'CERERE SOLICITANT', 13: 'ACT', 14: 'CAEN', 15: 'CAEN',
    16: 'INSTIT', 17: 'SEMN ACT SEDIU CAEN', 18: 'NERESTATAT', 19: 'INSTIT BEN_REAL ASOC_ID', 20: 'CAEN SEDIU ASOC_ID',
    21: 'ASOC_ID ACT INSTIT', 22: 'ASOC_ID CAEN SEDIU', 23: 'CERERE ASOC_ID', 24: 'ASOC_ID', 25: 'SOLICITANT', 26: 'SOLICITANT',
    27: 'SOLICITANT CAPITAL', 28: 'NERESTATAT', 29: 'ACT INSTIT', 30: 'CAEN SEDIU', 31: 'CAEN SEMN', 32: 'FARA_OBIECT', 33: 'ACT',
    34: 'SEDIU', 35: 'SEDIU CERERE', 36: 'SOLICITANT', 37: 'SOLICITANT', 38: 'SOLICITANT', 39: 'CAEN SEDIU CERERE', 40: 'ACT CAEN',
    41: 'SEDIU', 42: 'ASOC_ID SEDIU ACT', 43: 'FARA_OBIECT', 44: 'CAEN ACT ASOC_ID TARIF CERERE SEDIU', 45: 'INSTIT', 46: 'CAEN',
    47: 'CAPITAL ACT CERERE ASOC_ID', 48: 'SEDIU ASOC_ID', 49: 'TARIF CAEN', 50: 'CAEN',
}
MANUAL2 = {k: frozenset(v.split()) - {'NERESTATAT'} for k, v in MANUAL2.items()}
MECH2 = {k: ('M_DIRECT' if k in {4, 15, 19, 20, 50} else 'M_PARTIAL' if k in {7, 21, 39} else 'M_NEREMEDIAT') for k in range(1, 51)}
