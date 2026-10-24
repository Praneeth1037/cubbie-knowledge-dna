"""Validated prerequisite DAG. No network or third-party dependencies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class KnowledgeGraph:
    def __init__(self, data: dict):
        self.nodes = data["concepts"]
        if not isinstance(self.nodes, dict) or not self.nodes:
            raise ValueError("concepts must be a nonempty object")
        self.aliases = data.get("aliases", {})
        for key, node in self.nodes.items():
            dependencies = node.get("prerequisites", [])
            if not isinstance(dependencies, list) or len(set(dependencies)) != len(dependencies):
                raise ValueError(f"Invalid prerequisites for {key}")
            for dependency in dependencies:
                if dependency not in self.nodes:
                    raise ValueError(f"Unknown prerequisite: {dependency}")
        for key in self.nodes:
            self.prerequisites(key)  # also rejects disconnected cycles
        for target in self.aliases.values():
            if target not in self.nodes:
                raise ValueError(f"Unknown alias target: {target}")

    @classmethod
    def load(cls, path: Path | None = None) -> "KnowledgeGraph":
        return cls(json.loads((path or DATA_DIR / "transformer_concepts.json").read_text()))

    def resolve(self, concept: str) -> str:
        if not isinstance(concept, str):
            raise ValueError("Concept must be a string")
        normalized = concept.strip().lower().replace(" ", "_")
        normalized = self.aliases.get(normalized, normalized)
        if normalized not in self.nodes:
            raise ValueError(f"Unsupported concept: {concept}")
        return normalized

    def prerequisites(self, concept: str) -> list[str]:
        """Return transitive prerequisites in deterministic learning order."""
        concept = self.resolve(concept)
        visiting, visited, order = set(), set(), []

        def visit(key: str) -> None:
            if key in visiting:
                raise ValueError(f"Cycle detected at {key}")
            if key in visited:
                return
            visiting.add(key)
            for dependency in self.nodes[key].get("prerequisites", []):
                visit(dependency)
            visiting.remove(key)
            visited.add(key)
            order.append(key)

        visit(concept)
        return order[:-1]

    def learning_order(self, concept: str) -> list[str]:
        concept = self.resolve(concept)
        return self.prerequisites(concept) + [concept]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prerequisites", "order"])
    parser.add_argument("concept")
    args = parser.parse_args()
    try:
        graph = KnowledgeGraph.load()
        result = (graph.prerequisites(args.concept) if args.action == "prerequisites"
                  else graph.learning_order(args.concept))
        print(json.dumps({"ok": True, "concepts": result}))
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"ok": False, "error": {"code": "invalid_graph", "message": str(exc)}}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
