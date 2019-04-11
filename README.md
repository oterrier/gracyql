# gracyql
A thin GraphQL wrapper around spacy


## Requirements
Python 3.6+

## Description
An example of a basic [Starlette](https://github.com/encode/starlette) app using [Spacy](https://github.com/explosion/spaCy) and [Graphene](https://github.com/graphql-python/graphene).

The main goal is to be able to use the amazing power of spacy from other languages and retrieving only the information you need thanks to the GraphQL query definition.

The GraphQL schema tries to mimic as much as possible the original Spacy API with classes Doc, Span and Token

A simple batch processing with pagination of results is also implemented

### Doc
![Doc](images/doc.png?raw=true "GraphiQL result")
### Span
![Span](images/span.png?raw=true "GraphiQL result")
### Token
![Token](images/token.png?raw=true "GraphiQL result")


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

## Tests

- From the virtualenv
```
pytest
```

## Running

- From the virtualenv
```
python -m app.main
```

## Clients
- Kotlin : see [gracyql-kotlin](https://github.com/oterrier/gracyql-kotlin) 

## GraphQL queries

Navigate to [http://localhost:8990](http://localhost:8990) in your browser to access the GraphiQL console to start making queries.
Or [http://localhost:8990/schema](http://localhost:8990/schema) to introspect the GraphQL schema

### Simple POS TaggerQuery:

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


### Simple POS TaggerQuery including sentence level:

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


### Simple Dependency  Parser Query

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


### Simple NER Query

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

### Query with some pipes disabled
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
![ParserDisabledQuery](images/disabled.png?raw=true "GraphiQL result")


### Model metadata Query
```
query ModelMetaQuery {
  nlp(model: "en") {
    meta {
      author
      description
      lang
      license
      name
      pipeline
      sources
      spacy_version
      version
    }
  }
}
```
![ModelMetaQuery](images/meta.png?raw=true "GraphiQL result")


### Multi documents Query
```
query MultidocsQuery {
  nlp(model: "en") {
    batch(texts: [
      "Hello world1!",
      "Hello world2!",
      "Hello world3!",
      "Hello world4!",
      "Hello world5!",
      "Hello world6!",
      "Hello world7!",
      "Hello world8!",
      "Hello world9!",
      "Hello world10!"]) {
      docs {
        text
      }
    }
  }
}
```


### Batch multi documents Query
#### First call must have
- the list of texts to process
- batch_size : the size of the batch to achieve multi threading speedups with spaCy nlp.pipe
- next : the number of documents to retrieve as result of the query (next < batch_size of course)
```
query BatchMultidocsQuery {
  nlp(model: "en") {
    batch(texts: [
      "Hello world1!",
      "Hello world2!",
      "Hello world3!",
      "Hello world4!",
      "Hello world5!",
      "Hello world6!",
      "Hello world7!",
      "Hello world8!",
      "Hello world9!",
      "Hello world10!"],
    batch_size : 10, next : 2) {
      batch_id
      docs {
        text
      }
    }
  }
}
```
The result contains a batch_id UUID that will be used in subsequent calls
```{
  "data": {
    "nlp": {
      "batch": {
        "batch_id": "5654106e-62a7-4847-80e6-7ba3d0ec7b6a",
        "docs": [
          {
            "text": "Hello world1!"
          },
          {
            "text": "Hello world2!"
          }
        ]
      }
    }
  },
  "errors": null
}
```
![BatchMultidocsQuery1](images/bacth1.png?raw=true "GraphiQL result")

#### Subsequent calls must have
- batch_id : the UUID referencing the previous batch
- next : the number of documents to retrieve as result of the query
```
query BatchMultidocsQuery {
  nlp(model: "en") {
    batch(batch_id: "5654106e-62a7-4847-80e6-7ba3d0ec7b6a",
      next : 2) {
      batch_id
      docs {
        text
      }
    }
  }
}
```
The result contains the next 2 documents
```
{
  "data": {
    "nlp": {
      "batch": {
        "batch_id": "5654106e-62a7-4847-80e6-7ba3d0ec7b6a",
        "docs": [
          {
            "text": "Hello world3!"
          },
          {
            "text": "Hello world4!"
          }
        ]
      }
    }
  },
  "errors": null
}
```
![BatchMultidocsQuery2](images/bacth2.png?raw=true "GraphiQL result")

And you can issue the same query again and again until the batch is exhausted
