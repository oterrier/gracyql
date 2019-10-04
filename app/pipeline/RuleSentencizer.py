from collections import defaultdict

import plac
import spacy
from spacy.matcher.matcher import Matcher
from spacy.tokens.doc import Doc


class RuleSentencizer(object):
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
    overrides["rule_sentencizer"]["split"] = [
        # Split on double line breaks
        [{"IS_SPACE": True, "TEXT": { "REGEX" : "[\n]{2,}" }}, {}],
        # Split on hard punctuation
        [{"ISPUNCT": True, "TEXT" : { "IN" : [".", "!", "?"]}}, {}]
    ]
    overrides["rule_sentencizer"]["join"] = [
        # Une indemnité de 100. 000 Frs
        [{"IS_DIGIT": True}, {"IS_SENT_START": True, "IS_PUNCT" : True}, {"IS_DIGIT": True}]
    ]
    nlp = spacy.load(model)
    custom = RuleSentencizer(nlp, **overrides)
    nlp.add_pipe(custom)
    """
    name = "rule_sentencizer"
    split_matcher = None
    join_matcher = None
    def __init__(self, nlp, **cfg):
        if self.name in cfg:
            split_patterns = cfg[self.name].get('split', None)
            if split_patterns:
                self.split_matcher = Matcher(nlp.vocab)
                self.split_matcher.add("split", None, *split_patterns)
            join_patterns = cfg[self.name].get('join', None)
            if join_patterns:
                self.join_matcher = Matcher(nlp.vocab)
                self.join_matcher.add("join", None, *join_patterns)

    def __call__(self, doc : Doc):
        save_parsed = doc.is_parsed
        doc.is_parsed = False
        if self.split_matcher:
            matches = self.split_matcher(doc)
            for match_id, start, end in matches:
                token = doc[end-1]
                token.is_sent_start = True
                if end-2>=0 and doc[end-2].is_sent_start is True:
                    doc[end-2].is_sent_start = False
        if self.join_matcher:
            matches = self.join_matcher(doc)
            for match_id, start, end in matches:
                # If there is a sent start in the match, just remove it
                for token in doc[start:end]:
                    if token.is_sent_start:
                        token.is_sent_start = False
        if doc.is_sentenced:
            # Trim starting spaces
            sent_start = None
            for sent in doc.sents:
                sentlen = len(sent)
                first_non_space = 0
                while first_non_space < sentlen and sent[first_non_space].is_space:
                    first_non_space += 1
                if first_non_space > 0 and first_non_space < sentlen:
                    sent[0].is_sent_start = False
                    sent[first_non_space].is_sent_start = True

        doc.is_parsed = save_parsed if doc.is_sentenced else True
        return doc


def main():
    text = "toto\net titi"
    #text = "L'annonce du divorce de Sarkozy \"aurait pu se faire plus tôt\": Hollande \n \nMULHOUSE, 18 oct 2007 (AFP) \n \nL'annonce du divorce de Sarkozy \"aurait pu se faire plus tôt\": Hollande \n \nL'annonce du divorce de Nicolas et Cécilia Sarkozy \"aurait pu se faire plus tôt\", a estimé jeudi le premier secrétaire du Parti socialiste pour qui \"il fallait qu'il y ait une clarification\". \n \n\"Désormais, il n'y aura plus de questions qui seront posées\", a souligné M. Hollande, lors d'une conférence de presse organisée en marge d'une visite à la fédération du PS du Haut-Rhin. \n \n\"Cette annonce aurait pu se faire plus tôt. Mais je veux croire à la coïncidence\" avec le mouvement de grève de jeudi dans le pays, a-t-il dit. \n \n\"Aujourd'hui, l'information principale n'est pas le divorce de M. et Mme Sarkozy, c'est la grève particulièrement suivie qui a donné l'espoir qu'après ce mouvement il puisse y avoir une vraie négociation\".\nM. Hollande a aussi estimé que \"M. Sarkozy est un homme comme les autres\". \"Il a fait un choix personnel et sa vie privée mérite protection\", a-t-il dit."
    overrides = defaultdict(dict)
    overrides["rule_sentencizer"]["split"] = [
        # Split on double line breaks
        [{"IS_SPACE": True, "TEXT": { "REGEX" : "([\r]?[\n]){2,}" }}, {}],
        # Split on hard punctuation
        [{"ISPUNCT": True, "TEXT" : { "IN" : [".", "!", "?"]}}, {}],
        # Split on full stop if not followed by lower case letter or digit
        [{"ISPUNCT": True, "TEXT": "."}, {"SHAPE": { "REGEX" : "^[^xd]" }}]
    ]
    nlp = spacy.load("fr", disable=['ner', 'parser'])
    custom = RuleSentencizer(nlp, **overrides)
    nlp.add_pipe(custom)
    doc = nlp(text)
    for sent in doc.sents:
        print("<%s>"%sent.text)

if __name__ == "__main__":
    plac.call(main)