import asyncio

import graphene
import rx
import spacy
from graphene.types.resolver import dict_resolver


def spacy_attr_resolver(attname, default_value, root, info, **args):
    if hasattr(root, attname + '_'):
        return getattr(root, attname + '_', default_value)
    else:
        return getattr(root, attname, default_value)


class SpacyModels:
    def __init__(self):
        self.models = {}

    def get_model(self, model):
        return self.models.setdefault(model, spacy.load(model))


spacy_models = SpacyModels()


class Container(graphene.Interface):
    text = graphene.String(description="Verbatim text content.")
    text_with_ws = graphene.String(description="Text content, with trailing space character if present.")
    sentiment = graphene.Float(description="""A scalar value indicating the positivity or negativity of the object.""")
    has_vector = graphene.Boolean(
        description="""A boolean value indicating whether a word vector is associated with the object.""")
    vector = graphene.List(graphene.Float, description="A real-valued meaning representation.")
    vector_norm = graphene.Float(description="""The L2 norm of the document’s vector representation.""")

    def resolve_vector(self, info):
        return [float(x) for x in self.vector]


class Token(graphene.ObjectType):
    """An individual token — i.e. a word, punctuation symbol, whitespace, etc."""

    class Meta:
        interfaces = (Container,)
        default_resolver = spacy_attr_resolver

    id = graphene.Int(description="The index of the token within the parent document.")

    def resolve_id(self, info):
        return self.i

    start = graphene.Int(description="The starting character offset of the token within the parent document.")

    def resolve_start(self, info):
        return self.idx

    end = graphene.Int(description="The ending character offset of the token within the parent document.")

    def resolve_end(self, info):
        return self.idx + len(self)

    orth = graphene.String(description="""Verbatim text content (identical to Token.text).
    Exists mostly for consistency with the other attributes.""")
    pos = graphene.String(description="Coarse-grained part-of-speech.")
    tag = graphene.String(description="Fine-grained part-of-speech.")
    lemma = graphene.String()
    whitespace = graphene.String()
    ent_type = graphene.String()
    ent_iob = graphene.String()
    norm = graphene.String()
    lower = graphene.String()
    shape = graphene.String()
    prefix = graphene.String()
    suffix = graphene.String()
    is_sent_start = graphene.Boolean()
    is_alpha = graphene.Boolean()
    is_ascii = graphene.Boolean()
    is_digit = graphene.Boolean()
    is_lower = graphene.Boolean()
    is_upper = graphene.Boolean()
    is_title = graphene.Boolean()
    is_punct = graphene.Boolean()
    is_left_punct = graphene.Boolean()
    is_right_punct = graphene.Boolean()
    is_space = graphene.Boolean()
    is_bracket = graphene.Boolean()
    is_quote = graphene.Boolean()
    is_currency = graphene.Boolean()
    like_url = graphene.Boolean()
    like_num = graphene.Boolean()
    like_email = graphene.Boolean()
    is_oov = graphene.Boolean()
    is_stop = graphene.Boolean()
    dep = graphene.String()
    lang = graphene.String()
    prob = graphene.Float()
    cluster = graphene.Int()
    # Token references
    head = graphene.Field(lambda: Token)
    left_edge = graphene.Field(lambda: Token)
    right_edge = graphene.Field(lambda: Token)
    children = graphene.List(lambda: Token)
    ancestors = graphene.List(lambda: Token)
    conjuncts = graphene.List(lambda: Token)
    subtree = graphene.List(lambda: Token)
    rights = graphene.List(lambda: Token)
    lefts = graphene.List(lambda: Token)


class Span(graphene.ObjectType):
    """A slice from a Doc object."""

    class Meta:
        interfaces = (Container,)
        default_resolver = spacy_attr_resolver

    start = graphene.Int()

    def resolve_start(self, info):
        return self.start_char

    end = graphene.Int()

    def resolve_end(self, info):
        return self.end_char

    label = graphene.String()
    lemma = graphene.String()
    # Span references
    ents = graphene.List(lambda: Span)
    # Token references
    tokens = graphene.List(Token)

    def resolve_tokens(self, info):
        return list(self)

    root = graphene.Field(Token)
    conjuncts = graphene.List(Token)
    subtree = graphene.List(Token)
    rights = graphene.List(Token)
    lefts = graphene.List(Token)


class Cat(graphene.ObjectType):
    """Categories applied to whole document (label, score), or to spans (start, end, label, score)."""
    start = graphene.Int()

    def resolve_start(self, info):
        if isinstance(self[0], tuple):
            return self[0][0]
        else:
            return 0

    end = graphene.Int()

    def resolve_end(self, info):
        if isinstance(self[0], tuple):
            return self[0][1]
        else:
            return 0

    label = graphene.String()

    def resolve_end(self, info):
        if isinstance(self[0], tuple):
            return self[0][2]
        else:
            return str(self[0])

    score = graphene.Float()

    def resolve_score(self, info):
        return self[1]


class Doc(graphene.ObjectType):
    """A container for accessing linguistic annotations.
    Access sentences and named entities."""

    class Meta:
        interfaces = (Container,)

    tokens = graphene.List(Token, description="The tokens of the document.")

    def resolve_tokens(self, info):
        return list(self)

    sents = graphene.List(Span, description="""The the sentences in the document.
    Sentence spans have no label. To improve accuracy on informal texts, spaCy calculates sentence boundaries from the syntactic dependency parse.
    If the parser is disabled, the sents iterator will be unavailable.""")

    def resolve_sents(self, info):
        return list(self.sents)

    ents = graphene.List(Span,
                         description="The named entities in the document. Returns a list of named entity Span objects, if the entity recognizer has been applied.")

    def resolve_ents(self, info):
        return list(self.ents)

    noun_chunks = graphene.List(Span,
                                description="""The base noun phrases in the document.
    Returns a list of base noun-phrase Span objects, if the document has been syntactically parsed.
    A base noun phrase, or “NP chunk”, is a noun phrase that does not permit other NPs to be nested within it – so no NP-level coordination, no prepositional phrases, and no relative clauses.""")

    def resolve_noun_chunks(self, info):
        return list(self.noun_chunks)

    cats = graphene.List(Cat)

    def resolve_cats(self, info):
        return list(self.cats.items())


class ModelMeta(graphene.ObjectType):
    class Meta:
        default_resolver = dict_resolver

    author = graphene.String()
    def resolve_author(self, info, text):
        return self['nlp'].meta
    description = graphene.String()
    lang = graphene.String()
    license = graphene.String()
    name = graphene.String()
    pipeline = graphene.List(graphene.String)
    sources = graphene.List(graphene.String)
    spacy_version = graphene.String()
    version = graphene.String()


class Nlp(graphene.ObjectType):
    """A text-processing pipeline"""
    meta = graphene.Field(ModelMeta)
    def resolve_meta(self, info):
        return self['nlp'].meta

    doc = graphene.Field(Doc, text=graphene.String(required=True))

    def resolve_doc(self, info, text):
        return self['nlp'](text, disable=self['disable'])

    docs = graphene.List(Doc, texts=graphene.List(graphene.String, required=True),
                         batch_size=graphene.Int(default_value=50))

    def resolve_docs(self, info, texts, batch_size):
        return  self['nlp'].pipe(texts, batch_size=batch_size, disable=self['disable'])


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    nlp = graphene.Field(Nlp, model=graphene.String(required=False, default_value='en'),
                         disable=graphene.List(graphene.String, required=False, default_value=[]))

    def resolve_nlp(self, info, model, disable):
        return { 'nlp' : spacy_models.get_model(model), 'disable' : disable }


schema = graphene.Schema(query=Query, auto_camelcase=False)
