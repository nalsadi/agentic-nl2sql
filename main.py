import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.config.settings import validate_config, get_openai_client
from src.agent.react_agent import ReactAgent
from src.agent.llm_client import create_llm_client
from src.evaluation.test_runner import TestRunner
from src.utils.explorer import explorer

def create_agent() -> ReactAgent:
    if not validate_config():
        print("Configuration validation failed. Please check your settings.")
        sys.exit(1)
    
    openai_client = get_openai_client()
    llm_client = create_llm_client(openai_client)
    return ReactAgent(llm_client)

def cmd_explore(args):
    # Explore a database
    if args.list:
        explorer.list_available_databases()
        return
    
    if not args.database:
        print("Database name required for exploration")
        return
    
    if args.quick:
        explorer.quick_explore(args.database, args.max_tables or 3)
    else:
        explorer.explore_database(args.database)

def cmd_ask(args):
    # Ask a question 
    if not args.database or not args.question:
        print("Both database and question are required")
        return
    
    agent = create_agent()
    
    if args.enhanced:
        result = agent.run_enhanced(args.question, args.database, return_full_conversation=args.verbose)
        if args.verbose and isinstance(result, dict):
            print("\nFull conversation:")
            print(result.get('full_conversation', ''))
            if 'improved_sql' in result:
                print(f"\n🔧 Improved SQL: {result['improved_sql']}")
        else:
            print(f"\nAnswer: {result}")
    else:
        answer = agent.run(args.question, args.database)
        print(f"\nAnswer: {answer}")

def cmd_test(args):
    # Run benchmark tests 
    test_runner = TestRunner()
    
    spider_file = args.file or "spider_data/dev.json"
    
    if args.database:
        # Test specific database
        results = test_runner.run_database_specific_tests(
            args.database, 
            args.limit, 
            spider_file
        )
    elif args.enhanced:
        # Run enhanced tests
        results = test_runner.run_enhanced_tests(args.limit, spider_file)
    else:
        # Run basic tests
        results = test_runner.run_basic_tests(args.limit, spider_file)
    
    # Save results if requested
    if args.output:
        test_runner.save_results(results, args.output)

def cmd_compare(args):
    # Compare two SQL queries 
    if not all([args.database, args.expected, args.agent]):
        print("Database, expected SQL, and agent SQL are all required")
        return
    
    test_runner = TestRunner()
    comparison = test_runner.test_query_comparison(args.expected, args.agent, args.database)
    
    if comparison['match']:
        print("Queries return identical results!")
    else:
        print("Queries return different results")
        print(f"Details: {comparison['details']}")

def cmd_interactive():
    # Interactive mode 
    print("Spider SQL Agent - Interactive Mode")
    print("Type 'help' for commands, 'quit' to exit")
    
    agent = create_agent()
    current_db = None
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            elif command.lower() in ['help', 'h']:
                print("""
Commands:
  explore <db_name>          - Explore a database
  list                       - List available databases  
  use <db_name>             - Set current database
  ask <question>            - Ask a question about current database
  <question>                - Ask a question (if database is set)
  help                      - Show this help
  quit                      - Exit
""")
            
            elif command.startswith('explore '):
                db_name = command[8:].strip()
                explorer.quick_explore(db_name)
            
            elif command == 'list':
                explorer.list_available_databases()
            
            elif command.startswith('use '):
                current_db = command[4:].strip()
                print(f"📁 Current database set to: {current_db}")
            
            elif command.startswith('ask '):
                question = command[4:].strip()
                if not current_db:
                    print("No database selected. Use 'use <db_name>' first.")
                    continue
                answer = agent.run(question, current_db)
                print(f"Answer: {answer}")
            
            elif command and current_db:
                # Treat as a question
                answer = agent.run(command, current_db)
                print(f"Answer: {answer}")
            
            else:
                print("Unknown command. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Spider SQL Agent")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Explore command
    explore_parser = subparsers.add_parser('explore', help='Explore a database')
    explore_parser.add_argument('database', nargs='?', help='Database name to explore')
    explore_parser.add_argument('--list', action='store_true', help='List available databases')
    explore_parser.add_argument('--quick', action='store_true', help='Quick exploration (first few tables)')
    explore_parser.add_argument('--max-tables', type=int, help='Maximum tables to show in quick mode')
    
    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Ask a question')
    ask_parser.add_argument('database', help='Database name')
    ask_parser.add_argument('question', help='Question to ask')
    ask_parser.add_argument('--enhanced', action='store_true', help='Use enhanced agent with post-processing')
    ask_parser.add_argument('--verbose', action='store_true', help='Show full conversation')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare two SQL queries')
    compare_parser.add_argument('database', help='Database name')
    compare_parser.add_argument('expected', help='Expected SQL query')
    compare_parser.add_argument('agent', help='Agent SQL query') 

    # Test command
    test_parser = subparsers.add_parser('test', help='Run benchmark tests')
    test_parser.add_argument('--limit', type=int, default=5, help='Number of tests to run')
    test_parser.add_argument('--database', help='Test specific database only')
    test_parser.add_argument('--enhanced', action='store_true', help='Use enhanced agent')
    test_parser.add_argument('--file', help='Spider JSON file path')
    test_parser.add_argument('--output', help='Save results to file')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Start interactive mode')
    
    args = parser.parse_args()
    
    if args.command == 'explore':
        cmd_explore(args)
    elif args.command == 'ask':
        cmd_ask(args)
    elif args.command == 'test':
        cmd_test(args)
    elif args.command == 'compare':
        cmd_compare(args)
    elif args.command == 'interactive':
        cmd_interactive()
    else:
        # No command specified, start interactive mode
        cmd_interactive()

if __name__ == "__main__":
    main()
