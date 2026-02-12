<p align="center">
  <img src="./figs/biomni_logo.png" alt="Biomni Logo" width="600px" />
</p>

# Biomni: A General-Purpose Biomedical AI Agent

**Biomni** is a general-purpose biomedical AI agent that autonomously executes research tasks across diverse biomedical subfields. It integrates LLM reasoning with retrieval-augmented planning and code-based execution to enhance research productivity.

## Quick Start

```bash
# Install
pip install biomni

# Basic usage
from biomni.agent import A1
agent = A1(path="./data", llm="gpt-4")
agent.chat("Analyze differential gene expression between condition X and Y")
```

## Key Features

- 🧬 Multi-omics data integration and analysis
- 🤖 Autonomous research task execution
- 📊 Retrieval-augmented planning
- 🔧 200+ specialized biomedical tools
- 🗄️ Integration with major biological databases

## Documentation

- **[DEV_DOCS/INDEX.md](DEV_DOCS/INDEX.md)** - Complete documentation index
- **[Configuration Guide](docs/configuration.md)** - Setup and configuration
- **[Tutorials](tutorials/)** - Example notebooks and guides

## Community

- [Join our Slack](https://join.slack.com/t/biomnigroup/shared_invite/zt-3avks4913-dotMBt8D_apQnJ3mG~ak6Q)
- [Try Web UI](https://biomni.stanford.edu)
- [Follow on X](https://x.com/ProjectBiomni)
- [Paper](https://www.biorxiv.org/content/10.1101/2025.05.30.656746v1)

## Contributing

See [CONTRIBUTION.md](CONTRIBUTION.md) for guidelines.

## License

See [LICENSE](LICENSE) and [license_info.md](license_info.md) for details.

---

**Version**: 0.0.7+  
**Branch**: local-development-v1
