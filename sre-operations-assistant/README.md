# SRE Operations Assistant

GenAI-powered EC2 vulnerability management agent with MCP integration.

## Project Structure

```
sre-operations-assistant/
├── src/                    # Core MCP server and functions
├── infrastructure/         # Terraform and CDK code
├── cli/                   # MCP-powered CLI tool
├── bots/                  # Slack and Teams integrations
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation and runbooks
├── config/                # Configuration files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Deploy infrastructure: `cd infrastructure && terraform init && terraform apply`
3. Start MCP server: `python src/mcp_server.py`
4. Use CLI: `python cli/sre_cli.py --help`

## Components

- **MCP Server**: Core vulnerability management functions
- **CLI Tool**: Command-line interface with natural language support
- **Slack Bot**: `/sre-*` commands for team collaboration
- **Teams Bot**: Rich card notifications and approvals
- **Infrastructure**: Terraform-managed AWS resources

## Budget: $30-85/month | Timeline: 2 weeks