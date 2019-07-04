import random
import spacy
import plac
import psutil
import sys
import objgraph
import gc

gc.set_debug(gc.DEBUG_SAVEALL)

def load_data():
    return ["This is a fake test document number %d."%i for i in random.sample(range(10_000), 1_000)]


# def print_memory_usage():
#     print(objgraph.show_growth(limit=5))
#     print("GC count="+str(gc.get_count()))
#     gc.collect()

class ReloadableNlp:
    def __init__(self, model, reload=1000):
        self.model = model
        self.reload = reload
        self.count = 0
        self.nlp = spacy.load(model)

    def get_nlp(self):
        # self.count += 1
        # if self.count % self.reload == 0:
        #     del self.nlp
        #     gc.collect()
        #     self.nlp = spacy.load(self.model)
        return self.nlp



def parse_texts(reloadable, texts, iterations=10_000):
    for i in range(iterations):
        for doc in reloadable.get_nlp().pipe(texts, disable=['ner', 'parser']):
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
            #print_memory_usage()
            sys.stdout.flush()


if __name__ == '__main__':
    plac.call(main)
