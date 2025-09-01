# Architecture Diagrams

This directory contains Mermaid diagrams that visualize the architecture and components of the Spotify App Agent Template.

## Available Diagrams

### 1. [System Architecture](system-architecture.md)
High-level overview of the entire system architecture, showing how all components interact.

### 2. [Data Flow](data-flow.md)
Detailed flow of data through the system, from Spotify API to playlist updates.

### 3. [Authentication Flow](authentication-flow.md)
OAuth 2.0 authentication process and token management.

### 4. [Track Selection Process](track-selection.md)
How tracks are discovered, scored, and selected for playlists.

### 5. [Deployment Architecture](deployment.md)
Docker containerization and deployment structure.

## Viewing Diagrams

### Option 1: GitHub (Recommended)
GitHub natively supports Mermaid diagrams. Simply view the `.md` files on GitHub and the diagrams will render automatically.

### Option 2: Mermaid Live Editor
1. Copy the Mermaid code from any diagram file
2. Go to [Mermaid Live Editor](https://mermaid.live/)
3. Paste the code and see the diagram rendered

### Option 3: VS Code Extension
Install the "Mermaid Preview" extension in VS Code to view diagrams directly in the editor.

### Option 4: Local Rendering
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG from a diagram
mmdc -i system-architecture.md -o system-architecture.png
```

## Diagram Conventions

- **Components**: Rectangular boxes with rounded corners
- **External Services**: Hexagonal shapes
- **Data Stores**: Cylindrical shapes
- **Processes**: Rectangular boxes with straight corners
- **Decisions**: Diamond shapes
- **Data Flow**: Arrows showing direction of data movement

## Updating Diagrams

When making changes to the system architecture, please update the corresponding diagrams to maintain accuracy.

### Best Practices
- Keep diagrams simple and focused
- Use consistent naming conventions
- Include clear labels and descriptions
- Update diagrams when architecture changes
- Test diagrams render correctly on GitHub

## Diagram Sources

These diagrams are generated from the actual codebase and configuration files:
- `app/` - Application code structure
- `config/config.yaml` - Configuration schema
- `Dockerfile` - Container structure
- `Makefile` - Build and deployment processes
