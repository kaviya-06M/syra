import networkx as nx


class GraphTraversal:
    """
    Utility functions for walking the incident graph produced by
    GraphBuilder in order to locate the most likely root cause node(s).
    """

    def find_terminal_causes(self, graph):
        """
        Terminal causes are 'cause'/'symptom' nodes with no outgoing edges,
        i.e. the graph cannot be correlated any further downstream from
        them. These are the strongest root-cause candidates.
        """
        return [
            node for node, data in graph.nodes(data=True)
            if graph.out_degree(node) == 0 and data.get("type") != "anomaly"
        ]

    def find_path_to_cause(self, graph, cause):
        """Shortest path from the anomaly node down to a candidate cause."""
        try:
            return nx.shortest_path(graph, source="anomaly", target=cause)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def rank_causes_by_reachability(self, graph):
        """
        Ranks candidate causes by how many distinct symptoms lead to them.
        A cause reachable from multiple symptoms is more likely to be the
        true root cause.
        """
        ranking = {}

        symptoms = [n for n, d in graph.nodes(data=True) if d.get("type") == "symptom"]

        for node, data in graph.nodes(data=True):
            if data.get("type") != "cause":
                continue

            reach_count = sum(
                1 for symptom in symptoms if nx.has_path(graph, symptom, node)
            )
            ranking[node] = reach_count

        return dict(sorted(ranking.items(), key=lambda x: x[1], reverse=True))

    def get_upstream_symptoms(self, graph, cause):
        """Returns every symptom node that feeds into the given cause."""
        if cause not in graph:
            return []

        return [
            node for node in nx.ancestors(graph, cause)
            if graph.nodes[node].get("type") == "symptom"
        ]
