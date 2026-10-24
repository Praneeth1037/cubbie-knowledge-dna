import unittest

from scripts.knowledge_graph import KnowledgeGraph


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = KnowledgeGraph.load()

    def test_transitive_traversal_is_topological_and_unique(self):
        order = self.graph.learning_order("transformer_attention")
        self.assertEqual(len(order), 8)
        self.assertEqual(len(order), len(set(order)))
        for concept in order:
            for prerequisite in self.graph.nodes[concept]["prerequisites"]:
                self.assertLess(order.index(prerequisite), order.index(concept))

    def test_target_excluded_from_prerequisites(self):
        self.assertNotIn("attention_output", self.graph.prerequisites("attention_output"))
        self.assertEqual(self.graph.prerequisites("weighted_sums"), [])

    def test_aliases_and_unsupported_target(self):
        self.assertEqual(self.graph.resolve("Transformers"), "transformer_attention")
        self.assertEqual(self.graph.resolve("weighted sums"), "weighted_sums")
        with self.assertRaises(ValueError):
            self.graph.resolve("calculus")

    def test_cycle_detection(self):
        with self.assertRaisesRegex(ValueError, "Cycle"):
            KnowledgeGraph({"concepts": {"a": {"prerequisites": ["b"]}, "b": {"prerequisites": ["a"]}}})

    def test_disconnected_cycle_detection(self):
        with self.assertRaisesRegex(ValueError, "Cycle"):
            KnowledgeGraph({"concepts": {"ok": {}, "cycle": {"prerequisites": ["cycle"]}}})

    def test_unknown_and_duplicate_dependencies(self):
        for data in ({"a": {"prerequisites": ["missing"]}},
                     {"a": {}, "b": {"prerequisites": ["a", "a"]}}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                KnowledgeGraph({"concepts": data})


if __name__ == "__main__":
    unittest.main()
