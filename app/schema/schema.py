import itertools
import json
import uuid
from collections import defaultdict

import gc
import graphene
import spacy
from graphene.types.resolver import dict_resolver
from graphql import GraphQLError
from threading import RLock

from app.schema.SentenceCorrector import SentenceCorrector


def spacy_attr_resolver(attname, default_value, root, info, **args):
    if hasattr(root, attname + '_'):
        return getattr(root, attname + '_', default_value)
    else:
        return getattr(root, attname, default_value)


def load_model(model, cfg):
    overrides = json.loads(cfg) if cfg else {}
    # overrides2 = defaultdict(dict)
    # overrides2["sentence_corrector"]["rules"] = [
    #     # Une indemnité de 100. 000 Frs
    #     # Article 145-3 du code du commerce
    #     [{"IS_DIGIT": True}, {"IS_SENT_START": True, "IS_PUNCT" : True}, {"IS_DIGIT": True}],
    #     # Article L.145-3 du code du commerce
    #     [{"TEXT": {"REGEX": ".*[0-9]$"}}, {"IS_SENT_START": True, "IS_PUNCT": True}, {"IS_DIGIT": True}]
    # ]
    nlp = spacy.load(model, **overrides)
    custom = SentenceCorrector(nlp, **overrides)
    nlp.add_pipe(custom)
    return nlp


class SpacyModels:
    def __init__(self, reload):
        self.models = {}
        self.reload = reload
        self.rlock = RLock()

    def get_model(self, model, cfg):
        with self.rlock:
            key = (model, cfg)
            if key in self.models:
                nlp, count = self.models[key]
                if count % self.reload == 0:
                    del nlp
                    del self.models[key]
                    gc.collect()
                    nlp = load_model(model, cfg)
                    print("Model %s loaded/reloaded"%nlp.meta['name'])
                self.models[key] = (nlp, count+1)
            else:
                nlp = load_model(model, cfg)
                print("Model %s loaded/reloaded"%nlp.meta['name'])
                self.models[key] = (nlp, 1)
        return nlp

class BatchSlice:
    def __init__(self, doc_generator, max):
        self.uuid_ = uuid.uuid4()
        self.gen = doc_generator
        self.max = max
        self.id = 0

    def next(self, next):
        self.id += next
        return list(itertools.islice(self.gen, 0, next))

    def has_next(self):
        return self.id < self.max

class BatchDocs:
    def __init__(self):
        self.batches = {}

    def get(self, uuid_):
        if isinstance(uuid_, str):
            uuid_ = uuid.UUID(uuid_)
        return self.batches.get(uuid_, None)

    def add(self, batch : BatchSlice):
        self.batches[batch.uuid_] = batch

    def remove(self, batch : BatchSlice):
        if batch.uuid_ in self.batches:
            del self.batches[batch.uuid_]

spacy_models = SpacyModels(reload=100)
batch_docs = BatchDocs()


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

    id = graphene.Int(default_value=0)
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
    description = graphene.String()
    lang = graphene.String()
    license = graphene.String()
    name = graphene.String()
    pipeline = graphene.List(graphene.String)
    sources = graphene.List(graphene.String)
    spacy_version = graphene.String()
    version = graphene.String()


class Batch(graphene.ObjectType):
    class Meta:
        default_resolver = dict_resolver
    batch_id = graphene.UUID()
    docs = graphene.List(Doc)


class Nlp(graphene.ObjectType):
    """A text-processing pipeline"""
    meta = graphene.Field(ModelMeta)
    def resolve_meta(self, info):
        return self['nlp'].meta

    doc = graphene.Field(Doc, text=graphene.String(required=True))

    def resolve_doc(self, info, text):
        nlp = self['nlp']
        return nlp(text, disable=self['disable'])

    batch = graphene.Field(Batch, texts=graphene.List(graphene.String, required=False, default_value=None),
                         batch_id=graphene.String(required=False, default_value=None),
                         batch_size=graphene.Int(required=False, default_value=None),
                         next=graphene.Int(required=False, default_value=None)
                         )

    def resolve_batch(self, info, **args):
        nlp = self['nlp']
        if 'texts' in args:
            texts = args['texts']
            batch_size = args.get('batch_size', len(texts))
            batch_ = BatchSlice(nlp.pipe(texts, batch_size=batch_size, disable=self['disable']), len(texts))
            batch_docs.add(batch_)
        elif 'batch_id' in args:
            batch_ = batch_docs.get(args.get('batch_id'))
            if batch_:
                if not batch_.has_next():
                    batch_docs.remove(batch_)
            else:
                raise GraphQLError('Invalid batch_id %s or batch is exhausted!'%args.get('batch_id'))
        else:
            raise GraphQLError('One of texts or batch_id must be provided!')
        if batch_:
            batch_id = batch_.uuid_
            next = args.get('next', batch_.max)
            docs = batch_.next(next)
            if not batch_.has_next():
                batch_docs.remove(batch_)
            return { 'batch_id' : batch_id, 'docs' : docs }
        else:
            return None


class Query(graphene.ObjectType):
    nlp = graphene.Field(Nlp, model=graphene.String(required=False, default_value='en'),
                         disable=graphene.List(graphene.String, required=False, default_value=[]),
                         cfg=graphene.String(required=False, default_value='{}'))

    def resolve_nlp(self, info, model, disable, cfg):
        return { 'nlp' : spacy_models.get_model(model, cfg), 'disable' : disable }


schema = graphene.Schema(query=Query, auto_camelcase=False)
