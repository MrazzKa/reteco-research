"""Deterministic tie-breaking that does not depend on what a document id says.

Until week 4 every script broke exact score ties by doc id (ascending). In the Track-2
StackExchange corpora gold ids are `<question>_doc_<n>` and most negatives
`<question>_google_neg_<n>`, and "doc" < "google", so among exact duplicates the gold copy
would come first: a hidden use of the id (in practice it decided no result: those corpora
hold no exact duplicates; LOG 2026-10-26 13:24-13:42). The corpus file position is no better (gold
documents sit at the start of the file: mean relative position 0.007 in drones, 0.002 in
biology; LOG 2026-10-26 13:24). The neutral key is sha1(doc id): a fixed pseudo-random order.

    import tiebreak
    tiebreak.set_mode(args.tiebreak)          # "sha1" (default) or "id" (old behaviour)
    sorted(pairs, key=lambda x: (-x[1], tiebreak.key(x[0])))
"""
import hashlib
from functools import lru_cache

MODES = ("sha1", "id")
_mode = "sha1"


def set_mode(mode):
    global _mode
    assert mode in MODES, mode
    _mode = mode
    _sha1.cache_clear()


def mode():
    return _mode


@lru_cache(maxsize=None)
def _sha1(doc_id):
    return hashlib.sha1(doc_id.encode("utf-8")).hexdigest()


def key(doc_id):
    return _sha1(doc_id) if _mode == "sha1" else doc_id


def add_arg(ap):
    ap.add_argument("--tiebreak", default="sha1", choices=MODES,
                    help="order of exact score ties: sha1(doc id) (default) or doc id (weeks 1-4)")
