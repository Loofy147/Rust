import networkx as nx
import spacy
import pickle

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.nlp = spacy.load("en_core_web_sm")

    def add_entity(self, entity, attrs=None):
        self.graph.add_node(entity, **(attrs or {}))

    def add_relation(self, src, dst, relation, attrs=None):
        self.graph.add_edge(src, dst, key=relation, **(attrs or {}))

    def extract_from_text(self, text):
        doc = self.nlp(text)
        for ent in doc.ents:
            self.add_entity(ent.text, {"label": ent.label_})
        for token in doc:
            if token.dep_ == "ROOT" and token.head != token:
                self.add_relation(token.head.text, token.text, token.dep_)

    def query(self, entity):
        return list(self.graph.neighbors(entity))

    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.graph, f)

    def load(self, path):
        with open(path, "rb") as f:
            self.graph = pickle.load(f)