import networkx as nx

class PatternRecognizer:
    """ML-driven pattern recognition for codebase graph."""
    def __init__(self):
        self.patterns = {}
    def mine_patterns(self, graph: nx.DiGraph):
        # Example: find all triangles (motifs) in the graph
        triangles = [cycle for cycle in nx.simple_cycles(graph) if len(cycle) == 3]
        self.patterns['triangles'] = triangles
        return triangles
    def detect_anomalies(self, graph: nx.DiGraph):
        # Example: nodes with high degree or isolated nodes
        anomalies = {
            'high_degree': [n for n, d in graph.degree() if d > 5],
            'isolated': list(nx.isolates(graph))
        }
        return anomalies