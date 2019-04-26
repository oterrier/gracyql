import json
import random
from string import Template

from munch import munchify
from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ping():
    doc_text = "How are you Bob? What time is it in London?"
    response = query(
        """
        text
        """,
        doc_text)
    assert response.status_code == 200
    data = munchify(response.json()["data"])
    assert data.nlp.doc.text == doc_text


def test_tag():
    doc_text = "How are you Bob? What time is it in London?"
    response = query(
        """
        text
          tokens {
              id
              start
              end
              pos
              lemma
          }
        """,
        doc_text)
    assert response.status_code == 200
    data = munchify(response.json()["data"])
    assert data.nlp.doc.text == doc_text
    assert data.nlp.doc.tokens[0].lemma, "how"
    assert data.nlp.doc.tokens[0].pos, "ADV"


def test_tag_with_sentences():
    doc_text = "How are you Bob? What time is it in London?"
    response = query(
        """
        text
          sents {
              start
              end
              tokens {
                  id
                  start
                  end
                  pos
                  lemma
              }
          }
        """,
        doc_text)
    assert response.status_code == 200
    data = munchify(response.json()["data"])
    assert data.nlp.doc.text == doc_text
    assert data.nlp.doc.sents[0].tokens[0].lemma, "how"
    assert data.nlp.doc.sents[0].tokens[0].pos, "ADV"


def test_ner_with_sentences():
    doc_text = "How are you Bob? What time is it in London?"
    response = query(
        """
        text
          sents {
              start
              end
              ents {
                  start
                  end
                  text
                  label
              }
          }
        """,
        doc_text)
    assert response.status_code == 200
    data = munchify(response.json()["data"])
    assert data.nlp.doc.text == doc_text
    assert data.nlp.doc.sents[0].ents[0].text, "Bob"
    assert data.nlp.doc.sents[0].ents[0].label, "PERSON"
    assert data.nlp.doc.sents[1].ents[0].label, "GPE"


def test_bulk_tag():
    texts = ["This is test number %d."%i for i in random.sample(range(100_000), 103)]
    response = batchQuery(
        """
        text
          tokens {
              id
              start
              end
              pos
              lemma
          }
        """,
        texts)
    assert response.status_code == 200
    data = munchify(response.json()["data"])
    assert len(data.nlp.batch.docs) == 103
    assert data.nlp.batch.docs[0].text.startswith("This is test number")
    assert data.nlp.batch.docs[10].tokens[0].lemma, "how"
    assert data.nlp.batch.docs[20].tokens[0].pos, "ADV"
    assert data.nlp.batch.docs[20].tokens[4].pos, "NUM"


def query(docClause: str,
          document: str,
          model: str = "en",
          disable=[]):
    nlpClause = """nlp( model : %s, disable : %s)""" % (json.dumps(model), json.dumps(disable))
    batchClause = """doc( text : %s )""" % json.dumps(document)

    query = Template("""
            query {
              $nlpClause {
                $batchClause {
                    $docClause
                }
              }
            }
        """).substitute(nlpClause=nlpClause, batchClause=batchClause, docClause=docClause)
    return client.post('/', query, headers={"Content-Type": "application/graphql"})


def batchQuery(docsClause: str,
               documents=None,
               batchId=None,
               batchSize=None,
               next=None,
               model="en",
               disable=[]
               ):
    nlpClause = """nlp( model : %s, disable : %s)""" % (json.dumps(model), json.dumps(disable))
    batchArgs = []
    if documents:
        batchArgs.append("texts: %s" % json.dumps(documents))
    if batchId:
        batchArgs.append("batch_id: %s" % json.dumps(batchId))
    if batchSize:
        batchArgs.append("batch_size: %i" % batchSize)
    if next:
        batchArgs.append("next: %s" % next)
    batchClause = """batch( %s )""" % ','.join(batchArgs)

    query = Template("""
                query {
                  $nlpClause {
                    $batchClause {
                        batch_id
                        docs {
                            $docsClause
                        }
                    }
                  }
                }
            """).substitute(nlpClause=nlpClause, batchClause=batchClause, docsClause=docsClause)
    return client.post('/', query, headers={"Content-Type": "application/graphql"})

# def test_leak():
#     for i in range(100_000):
#         test_bulk_tag()