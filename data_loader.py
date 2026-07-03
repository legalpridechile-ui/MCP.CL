"""
Carga y utilidades de consulta sobre la ontología de cumplimiento VibeCodingChile.

La ontología combina:
- Ley N°21.719 (Protección de Datos Personales, Chile)
- ISO/IEC 42001 (Sistema de Gestión de IA)
- EU AI Act (Marco de riesgo)
- Terminología propia de Gobernador IA / VibeCodingChile

Fuente de datos: extraída de Gobernador IA / CheckWizard, complementada con
conceptos construidos para asegurar cobertura completa de los cuatro marcos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_ONTOLOGY_PATH = Path(__file__).parent / "ontology.json"


class OntologyStore:
    """Índice en memoria de la ontología, cargado una sola vez (modo local)."""

    def __init__(self, path: Path = _ONTOLOGY_PATH) -> None:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self.meta: Dict[str, Any] = raw["meta"]
        self.branches: List[Dict[str, Any]] = raw["branches"]
        self.concepts: Dict[str, Dict[str, Any]] = {
            c["id"]: c for c in raw["concepts"]
        }

        # Índice de hijos por parent_id
        self.children_index: Dict[str, List[str]] = {}
        for cid, c in self.concepts.items():
            parent = c.get("parent")
            if parent:
                self.children_index.setdefault(parent, []).append(cid)

    # ---------------------------------------------------------------- #
    # Búsqueda
    # ---------------------------------------------------------------- #
    def search(
        self,
        query: str,
        branch: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Búsqueda por coincidencia de texto en label (es/en), definición y aliases."""
        q = query.strip().lower()
        results = []
        for c in self.concepts.values():
            if branch and c["branch"] != branch:
                continue
            haystack = " ".join(
                [
                    c.get("label_es", ""),
                    c.get("label_en", ""),
                    c.get("definition_es", ""),
                    " ".join(c.get("aliases", [])),
                ]
            ).lower()
            if q in haystack:
                score = 2 if q in c.get("label_es", "").lower() else 1
                results.append((score, c))
        results.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in results[:limit]]

    def advanced_query(
        self,
        branch: Optional[str] = None,
        framework: Optional[str] = None,
        label_contains: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Filtros componibles sobre la ontología."""
        out = []
        for c in self.concepts.values():
            if branch and c["branch"] != branch:
                continue
            if framework and framework not in c.get("frameworks", []):
                continue
            if label_contains and label_contains.lower() not in c.get("label_es", "").lower():
                continue
            out.append(c)
        return out[:limit]

    # ---------------------------------------------------------------- #
    # Detalle y relaciones
    # ---------------------------------------------------------------- #
    def get(self, concept_id: str) -> Optional[Dict[str, Any]]:
        return self.concepts.get(concept_id)

    def get_children(self, concept_id: str) -> List[Dict[str, Any]]:
        return [self.concepts[cid] for cid in self.children_index.get(concept_id, [])]

    def get_parent(self, concept_id: str) -> Optional[Dict[str, Any]]:
        c = self.concepts.get(concept_id)
        if not c or not c.get("parent"):
            return None
        return self.concepts.get(c["parent"])

    def get_path(self, concept_id: str) -> List[Dict[str, Any]]:
        """Camino completo desde la raíz de la rama hasta el concepto."""
        path = []
        current = self.concepts.get(concept_id)
        while current:
            path.append(current)
            parent_id = current.get("parent")
            current = self.concepts.get(parent_id) if parent_id else None
        return list(reversed(path))

    def get_related(self, concept_id: str) -> Dict[str, Any]:
        c = self.concepts.get(concept_id)
        if not c:
            return {}
        return {
            "concept": c,
            "parent": self.get_parent(concept_id),
            "children": self.get_children(concept_id),
            "path": self.get_path(concept_id),
        }

    # ---------------------------------------------------------------- #
    # Ramas
    # ---------------------------------------------------------------- #
    def list_branches(self) -> List[Dict[str, Any]]:
        out = []
        for b in self.branches:
            count = sum(1 for c in self.concepts.values() if c["branch"] == b["id"])
            out.append({**b, "concept_count": count})
        return out

    def browse_branch(self, branch_id: str) -> List[Dict[str, Any]]:
        roots = [
            c for c in self.concepts.values()
            if c["branch"] == branch_id and c.get("parent") is None
        ]

        def build_tree(node: Dict[str, Any]) -> Dict[str, Any]:
            children = self.get_children(node["id"])
            return {
                "id": node["id"],
                "label_es": node["label_es"],
                "label_en": node.get("label_en", ""),
                "children": [build_tree(ch) for ch in children],
            }

        return [build_tree(r) for r in roots]


# Instancia global (modo local: se carga una sola vez al iniciar el server)
store = OntologyStore()
