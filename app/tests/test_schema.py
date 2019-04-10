from graphene.test import Client
from munch import munchify

from app.schema.schema import schema


def test_ping():
    client = Client(schema)
    executed = client.execute(
        '''{
              nlp(model: "en") {
                model
                doc(text: "Hello world!") {
                  text
                }
              }
            }''')
    nlp = munchify(executed["data"]).nlp
    assert nlp.model == "en"
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
    nsubjs = list(filter(lambda t: t.dep =="nsubj", roots[0].children))
    assert doc.tokens[nsubjs[1].id].lemma == "Bob"
    assert roots[1].id == 7
    assert roots[1].pos == "VERB"
    assert roots[1].lemma == "be"

