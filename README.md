# gracyql
A thin graphql wrapper around spacy
An example of a basic [Starlette](https://github.com/encode/starlette) app using [Spacy](https://github.com/explosion/spaCy) and [Graphene](https://github.com/graphql-python/graphene).

The main goal is to be able to use the amazing power of spacy from other languages and retrieving only the information you need thanks to the GraphQL query definition.

The GraphQL schema tries to mimic as much as possible the original Spacy API with classes Doc, Span and Token

## Doc
![Doc](images/doc.png?raw=true "GraphiQL result")
## Span
![Span](images/span.png?raw=true "GraphiQL result")
## Token
![Token](images/token.png?raw=true "GraphiQL result")

**Requirements**: Python 3.6+

## Setup

- Setup the dev environment and install the dependencies
```
./scripts/install
```

- Activate the virtualenv
```
. venv/bin/activate
```
- From the virtualenv, download your favorite spacy models

```
python -m spacy download en
```

## Running

- From the virtualenv
```
python -m app.main
```

## GraphQL queries

Navigate to `http://localhost:8990/` in your browser to access the GraphiQL console to start making queries.

Simple POS TaggerQuery:

```
fragment PosTagger on Token {
  id
  start
  end
  pos
  lemma
}

query PosTaggerQuery {
  nlp(model: "en") {
    doc(text: "How are you Bob? What time is it in London?") {
      text
      tokens {
        ...PosTagger
      }
    }
  }
}

```
![PosTaggerQuery](images/postagger.png?raw=true "GraphiQL result")

Simple POS TaggerQuery including sentence level:

```
fragment PosTagger on Token {
  id
  start
  end
  pos
  lemma
}

query PosTaggerWihtSentencesQuery {
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
}

```
![PosTaggerWihtSentencesQuery](images/postaggersents.png?raw=true "GraphiQL result")

Simple Dependency  Parser Query

```
query ParserQuery {
  nlp(model: "en") {
    doc(text: "How are you Bob? What time is it in London?") {
      text
      tokens {
        id
        start
        end
        pos
        lemma
        dep
        children {
          id
          dep
        }
      }
    }
  }
}

```
![ParserQuery](images/parser.png?raw=true "GraphiQL result")

Simple NER Query

```
query NERQuery {
  nlp(model: "en") {
    doc(text: "How are you Bob? What time is it in London?") {
      text
      ents {
        start
        end
        label
        text
      }
    }
  }
}

```
![NERQuery](images/ner.png?raw=true "GraphiQL result")

Multi documents Query

```
fragment PosTagger on Token {
  id
  start
  end
  pos
  lemma
}

query MultidocsQuery {
  nlp(model: "en") {
    docs(texts: ["Hello world1!", "Hello world2 !", "Hello world3!"], batch_size : 10) {
      text
      tokens {
        ...PosTagger
      }
    }
  }
}


```
![MultideryocsQu](images/multidocs.png?raw=true "GraphiQL result")



Query with some pipes disabled
```
query ParserDisabledQuery {
  nlp(model: "en", disable: ["parser", "ner"]) {
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
}
```
