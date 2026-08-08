import networkx as nx


class KnowledgeGraph:
    """
    Static domain knowledge describing how low-level symptoms relate to
    higher-level root causes on a Windows laptop/desktop. This is fixed
    domain knowledge (not the live incident graph, which GraphBuilder
    builds per-anomaly).
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build()

    def _build(self):
        edges = [
            ("high_cpu_usage", "runaway_process", 0.7),
            ("runaway_process", "cpu_bottleneck", 0.8),
            ("cpu_bottleneck", "system_slowdown", 0.9),

            ("high_memory_usage", "memory_leak", 0.6),
            ("memory_leak", "system_slowdown", 0.8),
            ("high_memory_usage", "excessive_swapping", 0.5),
            ("excessive_swapping", "system_slowdown", 0.7),

            ("low_disk_space", "disk_io_bottleneck", 0.6),
            ("disk_io_bottleneck", "system_slowdown", 0.6),

            ("high_network_traffic", "network_congestion", 0.6),
            ("network_congestion", "system_slowdown", 0.4),

            ("system_error_logged", "driver_or_service_failure", 0.4),
            ("driver_or_service_failure", "system_slowdown", 0.3),
        ]

        for source, target, weight in edges:
            self.graph.add_edge(source, target, weight=weight)

    def get_graph(self):
        return self.graph

    def get_related_causes(self, symptom):
        """Returns every downstream cause node reachable from a symptom."""
        if symptom not in self.graph:
            return []
        return list(nx.descendants(self.graph, symptom))

    def get_edge_weight(self, source, target):
        if self.graph.has_edge(source, target):
            return self.graph[source][target].get("weight", 0.0)
        return 0.0
