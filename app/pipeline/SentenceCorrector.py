from spacy.matcher.matcher import Matcher


class SentenceCorrector(object):
    """
    Simple component that correct some over-segmentation errors of the sentencizer using exception rules.
    Each rule must have a IS_SENT_START token pattern and this sentence boundary is removed from the final output.
    For example the text
    "Une indemnité de 100. 000 Frs"
    is by default segmented after the 100. but it shouldn't
    With this simple rule:
    [{"IS_DIGIT": True}, {"IS_SENT_START": True, "IS_PUNCT" : True}, {"IS_DIGIT": True}]
    The sentence corrector does the trick.

    The component is initialized this way:
    overrides = defaultdict(dict)
    overrides["sentence_corrector"]["rules"] = [
        # Une indemnité de 100. 000 Frs
        # Article 145-3 du code du commerce
        [{"IS_DIGIT": True}, {"IS_SENT_START": True, "IS_PUNCT" : True}, {"IS_DIGIT": True}],
        # Article L.145-3 du code du commerce
        [{"TEXT": {"REGEX": ".*[0-9]$"}}, {"IS_SENT_START": True, "IS_PUNCT": True}, {"IS_DIGIT": True}]
    ]
    nlp = spacy.load(model)
    custom = SentenceCorrector(nlp, **overrides)
    nlp.add_pipe(custom)
    """
    name = "sentence_corrector"

    def __init__(self, nlp, **cfg):
        self.matcher = Matcher(nlp.vocab)
        if self.name in cfg:
            patterns = cfg[self.name]['rules']
            self.matcher.add("SentenceCorrector", None, *patterns)

    def __call__(self, doc):
        matches = self.matcher(doc)
        if doc.is_parsed:
            doc.is_parsed = False
            for match_id, start, end in matches:
                # If there is a sent start in the match, just remove it
                for token in doc[start:end]:
                    if token.is_sent_start:
                        token.is_sent_start = False
            doc.is_parsed = True
        return doc

