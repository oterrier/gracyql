import random
import spacy
import plac
import psutil
import sys

def load_data():
    return ["This is a fake test document number %d."%i for i in random.sample(range(10_000), 1_000)]


class ReloadableNlp:
    def __init__(self, model, reload=1000):
        self.nlp = spacy.load(model)

    def get_nlp(self):
        return self.nlp



def parse_texts(reloadable, texts, iterations=10_000):
    for i in range(iterations):
        for doc in reloadable.get_nlp().pipe(texts):
            yield doc

@plac.annotations(
    iterations=("Number of iterations", "option", "n", int),
    model=("spaCy model to load", "positional", None, str)
)
def main(model='en_core_web_sm', iterations=10_000):
    texts = load_data()
    reloadable = ReloadableNlp(model)
    for i, doc in enumerate(parse_texts(reloadable, texts, iterations=iterations)):
        if i % 10_000 == 0:
            print(i, psutil.virtual_memory().percent)
            sys.stdout.flush()


if __name__ == '__main__':
    plac.call(main)
