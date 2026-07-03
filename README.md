# VibeCodingChile MCP Server

Servidor MCP (Model Context Protocol) que expone la ontología de cumplimiento de VibeCodingChile como herramientas, recursos y prompts para agentes de IA.

## Marcos normativos cubiertos

- **Ley N°21.719** - Protección de Datos Personales (Chile)
- **ISO/IEC 42001** - Sistema de Gestión de Inteligencia Artificial
- **EU AI Act** - Ley de Inteligencia Artificial de la Unión Europea
- **Gobernanza IA VibeCodingChile** - Terminología y herramientas propias

## Instalación

### Opción 1: Usando uvx (recomendado)

```bash
uvx vibecodingchile-mcp
```

### Opción 2: Instalación local con pip

```bash
pip install -e .
python -m server
```

### Opción 3: Docker

```bash
docker build -t vibecodingchile-mcp .
docker run -p 8000:8000 vibecodingchile-mcp
```

## Uso con Claude Code

Agregar el servidor MCP a Claude Code:

```bash
claude mcp add vibecodingchile -- uvx vibecodingchile-mcp
```

## Herramientas disponibles

| Herramienta | Descripción |
|-------------|-------------|
| `vcc_search_concept` | Busca conceptos por texto en etiquetas, definiciones y aliases |
| `vcc_advanced_query` | Consulta avanzada con filtros por rama, marco y etiqueta |
| `vcc_get_concept` | Obtiene detalle completo de un concepto por ID |
| `vcc_export_concept` | Exporta un concepto en markdown, JSON o JSON-LD |
| `vcc_list_branches` | Lista las ramas disponibles con conteo de conceptos |
| `vcc_browse_branch` | Explora el árbol jerárquico de una rama |
| `vcc_get_relations` | Obtiene padre, hijos y ruta taxonómica de un concepto |

## Recursos

- `vcc://ontology/full` - Ontología completa en JSON
- `vcc://ontology/concept/{concept_id}` - Concepto individual por ID
- `vcc://ontology/branch/{branch_id}` - Árbol jerárquico de una rama

## Prompts predefinidos

- `clasificar_documento_cumplimiento` - Clasifica documentos según la ontología
- `identificar_base_licitud` - Identifica base de licitud aplicable
- `evaluar_riesgo_eipd` - Evalúa si requiere EIPD y elementos necesarios
- `mapear_actor_cadena_responsabilidad` - Mapea actores en cadena IMDA
- `clasificar_riesgo_sistema_ia` - Clasifica riesgo según EU AI Act
- `mapear_control_iso42001` - Mapea procesos contra controles ISO 42001
- `redactar_documento_praxis` - Redacta documentos legales con plantillas

## Ramas de la ontología

1. **ley_21719** - Ley N°21.719 (Protección de Datos Chile)
2. **iso_42001** - ISO/IEC 42001 (Sistema de Gestión de IA)
3. **eu_ai_act** - EU AI Act (Marco de riesgo)
4. **gobernanza_ia** - Gobernanza IA VibeCodingChile

## Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Formatear código
black .
ruff check .
```

## Licencia

MIT License - Ver archivo LICENSE para más detalles.

## Autor

Matías Rojas Faúndez  
VibeCodingChile
