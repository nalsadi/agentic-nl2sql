# Agentic NL2SQL 

An agentic NL2SQL workflow powered with Azure OpenAI (see branches for Ollama integration). This agent can answer natural language questions by executing SQL queries against Spider benchmark databases. 

### Download Spider 

https://drive.google.com/file/d/1403EGqzIDoHMdQF4c9Bkyl7dZLZ5Wt6J/view

## TODO

- [ ] Migrate to LangChain
- [ ] Add optional Ollama integration (refactor inference pipeline)
- [ ] Large-scale evaluation



## Project Structure

```
agentic-nl2sql/
├── README.md
├── requirements.txt
├── src/
│   ├── config/
│   │   └── settings.py          # Configuration and Azure OpenAI setup
│   ├── prompts/
│   │   └── system_prompt.py     # ReAct system prompt templates
│   ├── tools/
│   │   ├── database.py          # Database connection and SQL execution
│   │   └── sql_optimizer.py     # SQL query post-processing
│   ├── agent/
│   │   ├── react_agent.py       # Main agent loop and ReAct logic
│   │   └── llm_client.py        # LLM interaction wrapper
│   ├── evaluation/
│   │   ├── spider_evaluator.py  # Spider benchmark evaluation
│   │   └── test_runner.py       # Test execution and reporting
│   └── utils/
│       └── explorer.py          # Database exploration utilities
├── spider_data/                 # Spider benchmark data
│   ├── database/
│   ├── dev.json
│   └── ...
└── main.py                      # CLI interface
```

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd agentic-nl2sql
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Azure OpenAI credentials**
   - Update `src/config/settings.py` with your Azure OpenAI endpoint and API key
   - Or use environment variables (recommended for production)

## Usage

### Command Line Interface

**Explore a database:**
```bash
python main.py explore concert_singer
```

**Ask a question:**
```bash
python main.py ask concert_singer "What is the song name and release year of the youngest singer?"
```

**Run benchmark tests:**
```bash
python main.py test --limit 10
```

### Programmatic Usage

```python
from src.agent.react_agent import ReactAgent
from src.config.settings import get_openai_client

# Initialize agent
client = get_openai_client()
agent = ReactAgent(client)

# Ask a question
answer = agent.run("What is the average age of singers?", db_name="concert_singer")
print(answer)
```

## Architecture

### ReAct Agent Pattern

The agent follows the ReAct (Reasoning and Acting) pattern:

1. **Thought**: Analyze the question and plan the SQL query
2. **Action**: Execute SQL query using the SQLQuery tool
3. **Observation**: Process the query results
4. **Repeat**: Continue until a complete answer is found
5. **Answer**: Provide the final response

### Key Components

- **ReAct Agent**: Core reasoning loop that generates and executes SQL queries
- **SQL Optimizer**: Post-processes queries for better accuracy on Spider benchmarks
- **Database Tools**: Secure SQLite query execution with error handling
- **Evaluation Suite**: Comprehensive testing against Spider benchmark data

## Configuration

### Azure OpenAI Settings

Update `src/config/settings.py`:

```python
AZURE_OPENAI_ENDPOINT = "your-endpoint"
AZURE_OPENAI_API_KEY = "your-api-key"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
```

### Environment Variables (Recommended)
For bash: 
```bash
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
```
For powershell:
```powershell
$env:AZURE_OPENAI_ENDPOINT = "your-endpoint"
$env:AZURE_OPENAI_API_KEY = "your-api-key"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
```

## Testing

Run the complete test suite:
```bash
python main.py test --limit 50
```

Test specific examples:
```bash
python main.py test --db concert_singer --limit 5
```

## Performance

The agent achieves strong performance on Spider benchmark examples through:

- **Smart Query Patterns**: Prefers `ORDER BY + LIMIT` over subqueries for min/max queries
- **Column Selection**: Only selects requested columns to match expected output
- **Error Recovery**: Handles database errors gracefully and suggests alternatives
- **Post-Processing**: Optimizes queries based on question patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Spider Dataset

This project uses the Spider dataset for SQL semantic parsing:
- Paper: [Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task](https://arxiv.org/abs/1809.08887)
- Website: https://yale-lily.github.io/spider
