import json

from graphene.test import Client
from munch import munchify

from app.schema.schema import schema


def test_ping():
    client = Client(schema)
    executed = client.execute(
        '''{
              nlp(model: "en") {
                meta {
                    lang
                }
                doc(text: "Hello world!") {
                  text
                }
              }
            }''')
    nlp = munchify(executed["data"]).nlp
    assert nlp.meta.lang == "en"
    doc = nlp.doc
    assert doc.text == "Hello world!"


def test_tag():
    client = Client(schema)
    executed = client.execute(
        '''fragment PosTagger on Token {
              id
              start
              end
              pos
              lemma
            }
            query PosTagger {
              nlp(model: "en") {
                doc(text: "How are you Bob? What time is it in London?") {
                  text
                  tokens {
                     ...PosTagger
                  }
                }
              }
            }''')
    nlp = munchify(executed["data"]).nlp
    doc = nlp.doc
    assert doc.text == "How are you Bob? What time is it in London?"
    assert doc.tokens[0].pos == "ADV"
    assert doc.tokens[0].lemma == "how"


def test_tag_with_sentences():
    client = Client(schema)
    executed = client.execute(
        '''fragment PosTagger on Token {
              id
              start
              end
              pos
              lemma
            }
            query PosTaggerWithSents {
              nlp(model: "en") {
                doc(text: "How are you Bob? What time is it in London?") {
                  text
                  sents {
                      start
                      end
                      text
                      tokens {
                         ...PosTagger
                      }
                  }
                }
              }
            }''')
    nlp = munchify(executed["data"]).nlp
    doc = nlp.doc
    assert doc.text == "How are you Bob? What time is it in London?"
    assert doc.sents[0].text == "How are you Bob?"
    assert doc.sents[0].tokens[0].lemma == "how"
    assert doc.sents[0].tokens[0].pos == "ADV"


def test_ner():
    client = Client(schema)
    executed = client.execute(
        '''query NER {
              nlp(model: "en") {
                doc(text: "How are you Bob? What time is it in London?") {
                  text
                  ents {
                      start
                      end
                      text
                      label
                  }
                }
              }
            }''')
    nlp = munchify(executed["data"]).nlp
    doc = nlp.doc
    assert doc.text == "How are you Bob? What time is it in London?"
    assert doc.ents[0].label == "PERSON"
    assert doc.ents[0].text == "Bob"
    assert doc.ents[1].label == "GPE"


def test_parse():
    client = Client(schema)
    executed = client.execute(
        '''fragment PosTagger on Token {
              id
              start
              end
              pos
              lemma
            }
            query Parser {
              nlp(model: "en") {
                doc(text: "How are you Bob? What time is it in London?") {
                  text
                  tokens {
                     ...PosTagger
                     dep
                     children {
                         id
                         dep
                     }
                  }
                }
              }
            }''')
    nlp = munchify(executed["data"]).nlp
    doc = nlp.doc
    assert doc.text == "How are you Bob? What time is it in London?"
    roots = list(filter(lambda t: t.dep == "ROOT", doc.tokens))
    assert len(roots) == 2
    assert roots[0].id == 1
    assert roots[0].pos == "VERB"
    assert roots[0].lemma == "be"
    nsubjs = list(filter(lambda t: t.dep == "nsubj", roots[0].children))
    assert doc.tokens[nsubjs[1].id].lemma == "Bob"
    assert roots[1].id == 7
    assert roots[1].pos == "VERB"
    assert roots[1].lemma == "be"


def test_multi_docs():
    client = Client(schema)
    texts = ["This is a test"] * 10
    executed = client.execute(
        """fragment PosTagger on Token {
              id
              start
              end
              pos
              lemma
            }
            query Parser {
              nlp(model: "en") {
                batch(texts: %s) {
                    docs {
                      text
                      tokens {
                         ...PosTagger
                         dep
                         children {
                             id
                             dep
                         }
                      }
                    }
                }
              }
            }""" % json.dumps(texts))
    nlp = munchify(executed["data"]).nlp
    docs = nlp.batch.docs
    assert len(docs) == 10


def test_batch():
    client = Client(schema)
    texts = ["This is a test. "] * 103
    first_query = """fragment PosTagger on Token {
              id
              start
              end
              pos
              lemma
            }
            query Parser {
              nlp(model: "en") {
                batch(texts: %s, batch_size : 10, next : 2 ) {
                    batch_id
                    docs {
                      text
                      tokens {
                         ...PosTagger
                         dep
                         children {
                             id
                             dep
                         }
                      }
                    }
                }
              }
            }""" % json.dumps(texts)
    executed = client.execute(first_query)
    nlp = munchify(executed["data"]).nlp
    docs = nlp.batch.docs
    total = len(docs)
    assert docs[0].text.startswith("This is a test")
    assert len(docs) == 2
    batch_id = nlp.batch.batch_id

    sub_query = """fragment PosTagger on Token {
              id
              start
              end
              pos
              lemma
            }
            query Parser {
              nlp(model: "en") {
                batch(batch_id : "%s", next : 10 ) {
                    batch_id
                    docs {
                      text
                      tokens {
                         ...PosTagger
                         dep
                         children {
                             id
                             dep
                         }
                      }
                    }
                }
              }
            }""" % batch_id

    has_more = "errors" not in executed
    while has_more:
        executed = client.execute(sub_query)
        has_more = "errors" not in executed and "data" in executed
        if has_more:
            nlp = munchify(executed["data"]).nlp
            has_more = nlp.batch
            if has_more:
                docs = nlp.batch.docs
                total += len(docs)
                assert docs[0].text.startswith("This is a test")
    assert total == 103


def test_disable():
    client = Client(schema)
    text = "This is a test"
    executed = client.execute(
        """query ParserDisabledQuery {
              nlp(model: "en", disable : ["parser", "ner"]) {
                doc(text: "I live in Grenoble, France") {
                  text
                  tokens {
                     id
                     pos
                     lemma
                     dep
                  }
                  ents {
                      start
                      end
                      label
                }
              }
            }
        }""")
    nlp = munchify(executed["data"]).nlp
    doc = nlp.doc
    assert doc.tokens[0].dep == ""
    assert len(doc.ents) == 0
