# Architecture Diagrams

Mermaid-based architecture diagrams for ArmPilot-AI.

## Diagram Overview

| Diagram | Purpose | Audience |
|---------|---------|----------|
| [System Context](system_context.md) | High-level system boundaries | All stakeholders |
| [Container](container.md) | Technical building blocks | Developers |
| [Component](component.md) | Backend internals | Engineers |
| [Deployment](deployment.md) | Infrastructure layout | DevOps |
| [Data Flow](data_flow.md) | Data movement | Architects |
| [Inference Flow](inference_flow.md) | Request processing | Developers |
| [Benchmark Flow](benchmark_flow.md) | Performance measurement | ML Engineers |
| [Optimization Flow](optimization_flow.md) | Auto-tuning process | ML Engineers |

## Viewing Diagrams

These diagrams use [Mermaid](https://mermaid.js.org/) syntax. You can view them:

1. **GitHub** — Renders automatically in Markdown files
2. **VS Code** — Use Mermaid preview extension
3. **Online** — Paste at [mermaid.live](https://mermaid.live)
4. **CLI** — Use `mmdc` (Mermaid CLI)

## Diagram Types

### C4 Model Diagrams

- **System Context** — Shows system boundaries and external actors
- **Container** — Technical building blocks and their interactions
- **Component** — Internal structure of containers

### Flow Diagrams

- **Data Flow** — How data moves through the system
- **Pipeline Flows** — Detailed processing steps

### Deployment Diagrams

- **Deployment** — Infrastructure and hosting

## Regenerating Diagrams

To update diagrams, edit the `.md` files directly. Mermaid syntax is rendered by:

- GitHub Markdown renderer
- Documentation generators (Docusaurus, VitePress)
- IDE plugins (VS Code, JetBrains)

## Diagram Conventions

- Use C4 model for architecture diagrams
- Use flowcharts for process flows
- Use ER diagrams for data models
- Color coding:
  - Green: Start/Entry points
  - Blue: End/Exit points
  - Red: Errors
  - Orange: Key decisions
