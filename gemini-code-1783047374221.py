"""
VibeCodingChile MCP Server
===========================

Expone la ontología de cumplimiento de VibeCodingChile (Ley N°21.719, ISO/IEC 42001,
EU AI Act y terminología propia de Gobernador IA) como herramientas, recursos y
prompts para agentes de IA vía Model Context Protocol.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
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
# Helpers de formato y Herramientas (TUS FUNCIONES ACTUALES AQUÍ)
# --------------------------------------------------------------------- #
# (Pega aquí el código de tus funciones _concept_to_md, vcc_advanced_query, etc.)



# --------------------------------------------------------------------- #
# Prompts de Negocio (El prompt de redacción de Praxis)
# --------------------------------------------------------------------- #
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
        f"5. REGLA DE ORO: No modifiques los fundamentos jurídicos, ni las referencias a la Ley N°21.719, ni el correo corporativo (Vibecodingchile.dev@vibecodingchile.cl) de la plantilla original.\n"
    )

# --------------------------------------------------------------------- #
# NUEVO: Recurso de Plantillas (Praxis Legal Comercial)
# --------------------------------------------------------------------- #
@mcp.resource("vcc://templates/praxis/{nombre_plantilla}")
async def get_template_resource(nombre_plantilla: str) -> str:
    """Lee y devuelve el contenido de una plantilla de praxis confidencial."""
    # Apunta a la carpeta 'templates' en la raíz del proyecto
    template_path = Path(__file__).parent / "templates" / nombre_plantilla
    
    if not template_path.exists():
        return f"Error de Sistema: La plantilla '{nombre_plantilla}' no se encuentra en el repositorio seguro de VibeCodingChile."
    
    return template_path.read_text(encoding="utf-8")

# --------------------------------------------------------------------- #
# NUEVO: Ejecución del Servidor Web (SSE) para Azure / SaaS
# --------------------------------------------------------------------- #
def main() -> None:
    # transport="sse" levanta un servidor HTTP real, esencial para Docker y la nube.
    mcp.run(transport="sse", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()