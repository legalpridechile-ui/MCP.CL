"""
VibeCodingChile MCP Server
===========================

Expone la ontología de cumplimiento de VibeCodingChile (Ley N°21.719, ISO/IEC 42001,
EU AI Act y terminología propia de Gobernador IA) como herramientas, recursos y
prompts para agentes de IA vía Model Context Protocol.

Uso rápido:
    uvx vibecodingchile-mcp

O agregar a Claude Code:
    claude mcp add vibecodingchile -- uvx vibecodingchile-mcp
"""

from __future__ import annotations

import json
from enum import Enum
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from .data_loader import store

mcp = FastMCP("vibecodingchile_mcp")


# --------------------------------------------------------------------- #
# Formatos de salida
# --------------------------------------------------------------------- #
class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class ExportFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    JSONLD = "jsonld"


# --------------------------------------------------------------------- #
# Helpers de formato
# --------------------------------------------------------------------- #
def _concept_to_md(c: dict, include_path: bool = False) -> str:
    lines = [f"### {c['label_es']} (`{c['id']}`)"]
    if c.get("label_en"):
        lines.append(f"*{c['label_en']}*")
    lines.append("")
    lines.append(c.get("definition_es", ""))
    if c.get("aliases"):
        lines.append(f"\n**Alias:** {', '.join(c['aliases'])}")
    lines.append(f"\n**Rama:** {c['branch']} | **Marcos:** {', '.join(c.get('frameworks', []))}")
    if include_path:
        path = store.get_path(c["id"])
        breadcrumb = " → ".join(p["label_es"] for p in path)
        lines.append(f"\n**Ruta taxonómica:** {breadcrumb}")
    return "\n".join(lines)


def _concept_to_jsonld(c: dict) -> dict:
    return {
        "@context": "https://vibecodingchile.dev/context/compliance-ontology.jsonld",
        "@id": f"vcc:{c['id']}",
        "@type": "ComplianceConcept",
        "skos:prefLabel": {"es": c["label_es"], "en": c.get("label_en", "")},
        "skos:definition": {"es": c.get("definition_es", "")},
        "skos:altLabel": c.get("aliases", []),
        "vcc:branch": c["branch"],
        "vcc:frameworks": c.get("frameworks", []),
        "skos:broader": f"vcc:{c['parent']}" if c.get("parent") else None,
    }


def _results_list_md(results: List[dict], title: str) -> str:
    if not results:
        return f"## {title}\n\nSin resultados."
    lines = [f"## {title} ({len(results)})\n"]
    for c in results:
        lines.append(f"- **{c['label_es']}** (`{c['id']}`) — {c.get('definition_es', '')[:140]}...")
    return "\n".join(lines)


# --------------------------------------------------------------------- #
# Input models
# --------------------------------------------------------------------- #
class SearchConceptInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., description="Texto a buscar en etiquetas, definiciones y alias (ej. 'base de licitud', 'high-risk AI')",
        min_length=1, max_length=200,
    )
    branch: Optional[str] = Field(
        default=None,
        description="Filtrar por rama: ley_21719, iso_42001, eu_ai_act, gobernanza_ia",
    )
    limit: int = Field(default=10, description="Máximo de resultados", ge=1, le=50)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class AdvancedQueryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    branch: Optional[str] = Field(default=None, description="Rama exacta a filtrar")
    framework: Optional[str] = Field(
        default=None,
        description="Marco normativo asociado: ley_21719, iso_42001, eu_ai_act, gobernanza_ia",
    )
    label_contains: Optional[str] = Field(default=None, description="Substring a buscar en la etiqueta en español")
    limit: int = Field(default=50, ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GetConceptInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    concept_id: str = Field(..., description="ID exacto del concepto (ej. 'base_licitud', 'riesgo_alto', 'checkwizard')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class ExportConceptInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    concept_id: str = Field(..., description="ID exacto del concepto a exportar")
    format: ExportFormat = Field(default=ExportFormat.MARKDOWN, description="Formato de exportación")


class BrowseBranchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    branch: str = Field(
        ..., description="ID de la rama: ley_21719, iso_42001, eu_ai_act, gobernanza_ia"
    )


class GetRelationsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    concept_id: str = Field(..., description="ID exacto del concepto")


# --------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------- #
@mcp.tool(
    name="vcc_search_concept",
    annotations={
        "title": "Buscar concepto de cumplimiento",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def vcc_search_concept(params: SearchConceptInput) -> str:
    """Busca conceptos de cumplimiento por etiqueta, definición o alias.

    Cubre Ley N°21.719 (protección de datos), ISO/IEC 42001 (gestión de IA),
    EU AI Act (marco de riesgo) y terminología propia de Gobernador IA
    (NORMA, CheckWizard, OpenFang, Trust Score, etc.).

    Args:
        params (SearchConceptInput): query, branch opcional, limit, response_format

    Returns:
        str: Lista de conceptos coincidentes en Markdown o JSON.
    """
    results = store.search(params.query, branch=params.branch, limit=params.limit)
    if params.response_format == ResponseFormat.JSON:
        return json.dumps(results, ensure_ascii=False, indent=2)
    return _results_list_md(results, f"Resultados para '{params.query}'")


@mcp.tool(
    name="vcc_advanced_query",
    annotations={
        "title": "Consulta avanzada con filtros",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def vcc_advanced_query(params: AdvancedQueryInput) -> str:
    """Ejecuta una consulta con filtros componibles sobre la ontología.

    Permite combinar filtros de rama, marco normativo y coincidencia de etiqueta,
    útil para tareas como "todos los conceptos de EU AI Act relacionados a riesgo alto"
    o "todo lo de terminología propia de gobernanza_ia".

    Args:
        params (AdvancedQueryInput): branch, framework, label_contains, limit, response_format

    Returns:
        str: Lista de conceptos filtrados en Markdown o JSON.
    """
    results = store.advanced_query(
        branch=params.branch,
        framework=params.framework,
        label_contains=params.label_contains,
        limit=params.limit,
    )
    if params.response_format == ResponseFormat.JSON:
        return json.dumps(results, ensure_ascii=False, indent=2)
    return _results_list_md(results, "Resultados de consulta avanzada")


@mcp.tool(
    name="vcc_get_concept",
    annotations={
        "title": "Obtener detalle de un concepto",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def vcc_get_concept(params: GetConceptInput) -> str:
    """Recupera el detalle completo de un concepto por su ID, incluyendo su ruta taxonómica.

    Args:
        params (GetConceptInput): concept_id, response_format

    Returns:
        str: Detalle del concepto en Markdown o JSON. Mensaje de error si no existe.
    """
    c = store.get(params.concept_id)
    if not c:
        return f"Error: no existe un concepto con id '{params.concept_id}'. Usa vcc_search_concept para encontrar el ID correcto."
    if params.response_format == ResponseFormat.JSON:
        payload = dict(c)
        payload["path"] = [p["id"] for p in store.get_path(params.concept_id)]
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return _concept_to_md(c, include_path=True)


@mcp.tool(
    name="vcc_export_concept",
    annotations={
        "title": "Exportar concepto",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def vcc_export_concept(params: ExportConceptInput) -> str:
    """Exporta un concepto en el formato solicitado para integración con otros sistemas.

    Formatos soportados: markdown (lectura humana), json (estructurado), jsonld (interoperable, SKOS-like).

    Args:
        params (ExportConceptInput): concept_id, format

    Returns:
        str: Representación del concepto en el formato pedido.
    """
    c = store.get(params.concept_id)
    if not c:
        return f"Error: no existe un concepto con id '{params.concept_id}'."
    if params.format == ExportFormat.MARKDOWN:
        return _concept_to_md(c, include_path=True)
    if params.format == ExportFormat.JSONLD:
        return json.dumps(_concept_to_jsonld(c), ensure_ascii=False, indent=2)
    return json.dumps(c, ensure_ascii=False, indent=2)


@mcp.tool(
    name="vcc_list_branches",
    annotations={
        "title": "Listar ramas de la taxonomía",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def vcc_list_branches() -> str:
    """Lista las ramas disponibles de la ontología con el conteo de conceptos por rama.

    Ramas: ley_21719, iso_42001, eu_ai_act, gobernanza_ia.

    Returns:
        str: Listado en Markdown de ramas con su conteo de conceptos.
    """
    branches = store.list_branches()
    lines = ["## Ramas de la ontología VibeCodingChile\n"]
    for b in branches:
        lines.append(f"- **{b['label_es']}** (`{b['id']}`) — {b['concept_count']} conceptos")
    return "\n".join(lines)


@mcp.tool(
    name="vcc_browse_branch",
    annotations={
        "title": "Explorar árbol de una rama",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def vcc_browse_branch(params: BrowseBranchInput) -> str:
    """Devuelve el árbol jerárquico completo (padre/hijo) de una rama de la ontología.

    Args:
        params (BrowseBranchInput): branch

    Returns:
        str: Árbol en JSON con estructura anidada de conceptos.
    """
    tree = store.browse_branch(params.branch)
    if not tree:
        return f"Error: la rama '{params.branch}' no existe o no tiene conceptos raíz. Usa vcc_list_branches para ver las ramas disponibles."
    return json.dumps(tree, ensure_ascii=False, indent=2)


@mcp.tool(
    name="vcc_get_relations",
    annotations={
        "title": "Obtener relaciones de un concepto",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def vcc_get_relations(params: GetRelationsInput) -> str:
    """Obtiene padre, hijos directos y ruta taxonómica completa de un concepto.

    Útil para entender dónde se ubica un concepto dentro de la jerarquía y qué
    conceptos relacionados existen (ej. bases de licitud específicas bajo 'base_licitud').

    Args:
        params (GetRelationsInput): concept_id

    Returns:
        str: Relaciones del concepto en JSON (parent, children, path).
    """
    rel = store.get_related(params.concept_id)
    if not rel:
        return f"Error: no existe un concepto con id '{params.concept_id}'."
    return json.dumps(rel, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------- #
# Resources
# --------------------------------------------------------------------- #
@mcp.resource("vcc://ontology/full")
async def get_full_ontology() -> str:
    """Ontología completa en JSON (todas las ramas y conceptos)."""
    return json.dumps(
        {"meta": store.meta, "branches": store.branches, "concepts": list(store.concepts.values())},
        ensure_ascii=False,
        indent=2,
    )


@mcp.resource("vcc://ontology/concept/{concept_id}")
async def get_concept_resource(concept_id: str) -> str:
    """Recurso individual de un concepto por ID."""
    c = store.get(concept_id)
    if not c:
        return json.dumps({"error": f"concept '{concept_id}' not found"})
    return json.dumps(c, ensure_ascii=False, indent=2)


@mcp.resource("vcc://ontology/branch/{branch_id}")
async def get_branch_resource(branch_id: str) -> str:
    """Árbol jerárquico de una rama como recurso."""
    tree = store.browse_branch(branch_id)
    return json.dumps(tree, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------- #
# Prompts
# --------------------------------------------------------------------- #
@mcp.prompt(name="clasificar-documento-cumplimiento")
def clasificar_documento_cumplimiento(texto_documento: str) -> str:
    """Clasifica un documento según la ontología de cumplimiento VibeCodingChile."""
    return (
        "Clasifica el siguiente documento usando la ontología de cumplimiento VibeCodingChile "
        "(herramientas vcc_search_concept / vcc_advanced_query). Identifica: "
        "(1) marco(s) normativo(s) aplicable(s) (ley_21719 / iso_42001 / eu_ai_act), "
        "(2) rama y concepto(s) taxonómico(s) más específico(s), "
        "(3) base de licitud aplicable si corresponde, "
        "(4) nivel de riesgo EU AI Act si el documento describe un sistema de IA.\n\n"
        f"Documento:\n{texto_documento}"
    )


@mcp.prompt(name="identificar-base-licitud")
def identificar_base_licitud(descripcion_tratamiento: str) -> str:
    """Identifica la base de licitud aplicable a un tratamiento de datos descrito."""
    return (
        "Usando vcc_browse_branch(branch='ley_21719') y vcc_get_concept, identifica la base de "
        "licitud (consentimiento, ejecución contractual, obligación legal, interés legítimo, etc.) "
        "más apropiada para el siguiente tratamiento de datos personales, justificando la elección "
        "y señalando riesgos si la base es débil o cuestionable.\n\n"
        f"Tratamiento descrito:\n{descripcion_tratamiento}"
    )


@mcp.prompt(name="evaluar-riesgo-eipd")
def evaluar_riesgo_eipd(descripcion_sistema: str) -> str:
    """Evalúa si un sistema requiere EIPD y qué elementos debe cubrir."""
    return (
        "Usando vcc_get_concept(concept_id='eipd') como referencia, evalúa si el siguiente sistema "
        "requiere una Evaluación de Impacto en la Protección de Datos (EIPD) bajo la Ley N°21.719, "
        "y en caso afirmativo, lista los elementos mínimos que debe cubrir la evaluación.\n\n"
        f"Sistema:\n{descripcion_sistema}"
    )


@mcp.prompt(name="mapear-actor-cadena-responsabilidad")
def mapear_actor_cadena_responsabilidad(descripcion_sistema_ia: str) -> str:
    """Mapea los actores y su responsabilidad en la cadena IMDA para un sistema de IA."""
    return (
        "Usando vcc_get_concept(concept_id='actor_cadena_responsabilidad') como marco de referencia, "
        "identifica los actores (proveedor, implementador, distribuidor, usuario) involucrados en el "
        "siguiente sistema de IA y asigna responsabilidad conforme al enfoque de cadena de "
        "responsabilidad (IMDA) integrado en la Ley N°21.719.\n\n"
        f"Sistema de IA:\n{descripcion_sistema_ia}"
    )


@mcp.prompt(name="clasificar-riesgo-sistema-ia")
def clasificar_riesgo_sistema_ia(descripcion_sistema_ia: str) -> str:
    """Clasifica un sistema de IA según los niveles de riesgo del EU AI Act."""
    return (
        "Usando vcc_browse_branch(branch='eu_ai_act'), clasifica el siguiente sistema de IA en uno de "
        "los niveles de riesgo (inaceptable, alto, limitado, mínimo) y detalla las obligaciones "
        "aplicables al proveedor y/o implementador según corresponda.\n\n"
        f"Sistema de IA:\n{descripcion_sistema_ia}"
    )


@mcp.prompt(name="mapear-control-iso42001")
def mapear_control_iso42001(descripcion_proceso: str) -> str:
    """Mapea un proceso organizacional contra los controles de ISO/IEC 42001."""
    return (
        "Usando vcc_browse_branch(branch='iso_42001'), identifica qué elementos del Sistema de "
        "Gestión de IA (SGIA) — roles, evaluación de riesgo, supervisión humana, ciclo de vida — "
        "aplican al siguiente proceso organizacional, señalando brechas de cumplimiento.\n\n"
        f"Proceso:\n{descripcion_proceso}"
    )

        f"Una vez tengas todos los datos, entrégame el documento final listo para firmar."
    )

@mcp.prompt(name="redactar-documento-praxis")
def redactar_documento_praxis(nombre_plantilla: str, contexto_caso: str = "") -> str:
    """Orquesta la redacción de un documento legal usando una plantilla de praxis."""
    return (
        f"Actúa como un agente legal experto en cumplimiento normativo y la praxis jurídica chilena.\n"
        f"Tu objetivo es redactar un documento final impecable basado estrictamente en una plantilla pre-aprobada.\n\n"
        f"Instrucciones:\n"
        f"1. Accede al recurso de la plantilla usando: vcc://templates/praxis/{nombre_plantilla}\n"
        f"2. Analiza el texto e identifica todas las variables ocultas entre corchetes (ej. [RUT_PARTE], [MONTO_CLP], [FECHA_DOCUMENTO]).\n"
        f"3. Revisa los datos iniciales proporcionados en este contexto: '{contexto_caso}'. Si los datos cubren las variables, reemplázalas inmediatamente.\n"
        f"4. Si falta ALGÚN dato para completar los corchetes, detente. Hazme una lista corta y directa de los datos que necesitas que te provea antes de redactar.\n"
        f"5. REGLA DE ORO: No modifiques los fundamentos jurídicos, ni las referencias a la Ley N°21.719, ni el correo corporativo (Vibecodingchile.dev@vibecodingchile.cl) de la plantilla original.\n\n"
        f"Una vez tengas todos los datos, entrégame el documento final listo para firmar."
    )

7def main() -> None:
    mcp.run()

if __name__ == "__main__":
    main()
