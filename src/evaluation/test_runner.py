import os
from typing import Optional
from ..config.settings import validate_config, get_openai_client
from ..agent.react_agent import ReactAgent
from ..agent.llm_client import create_llm_client
from .spider_evaluator import (
    load_spider_examples, 
    evaluate_agent_on_spider, 
    evaluate_enhanced_agent,
    print_evaluation_summary,
    save_evaluation_results)

class TestRunner:
    
    def __init__(self):
        if not validate_config():
            raise ValueError("Invalid configuration. Please check your settings.")
        
        # Initialize components
        openai_client = get_openai_client()
        llm_client = create_llm_client(openai_client)
        self.agent = ReactAgent(llm_client)
        
    def run_basic_tests(self, limit: int = 5, spider_file: str = "spider_data/dev.json") -> dict:
        print(f" Running basic tests with limit: {limit}")
        
        if not os.path.exists(spider_file):
            raise FileNotFoundError(f"Spider file not found: {spider_file}")
        
        examples = load_spider_examples(spider_file, limit)
        results = evaluate_agent_on_spider(self.agent, examples, limit)
        print_evaluation_summary(results)
        
        return results
    
    def run_enhanced_tests(self, limit: int = 5, spider_file: str = "spider_data/dev.json") -> dict:
        """Run enhanced agent tests with post-processing"""
        print(f" Running enhanced tests with limit: {limit}")
        
        if not os.path.exists(spider_file):
            raise FileNotFoundError(f"Spider file not found: {spider_file}")
        
        examples = load_spider_examples(spider_file, limit)
        results = evaluate_enhanced_agent(self.agent, examples, limit)
        print_evaluation_summary(results)
        
        return results
    
    def run_single_test(self, question: str, db_name: str, enhanced: bool = False) -> str:
        print(f" Testing single question on {db_name}")
        print(f"Question: {question}")
        
        if enhanced:
            result = self.agent.run_enhanced(question, db_name, return_full_conversation=True)
            return result.get('answer', 'No answer found')
        else:
            return self.agent.run(question, db_name)
    
    def run_database_specific_tests(self, db_name: str, limit: int = 5, spider_file: str = "spider_data/dev.json") -> dict:
        print(f" Running tests for database: {db_name}")
        
        if not os.path.exists(spider_file):
            raise FileNotFoundError(f"Spider file not found: {spider_file}")
        
        # Load and filter examples
        all_examples = load_spider_examples(spider_file)
        db_examples = [ex for ex in all_examples if ex['db_id'] == db_name]
        
        if not db_examples:
            print(f" No examples found for database: {db_name}")
            return {"total": 0, "successful": 0, "failed": 0, "details": []}
        
        print(f"Found {len(db_examples)} examples for {db_name}")
        examples = db_examples[:limit]
        
        results = evaluate_enhanced_agent(self.agent, examples, limit)
        print_evaluation_summary(results)
        
        return results
    
    def test_query_comparison(self, expected_sql: str, agent_sql: str, db_name: str) -> dict:
        from .spider_evaluator import test_single_query_comparison
        return test_single_query_comparison(expected_sql, agent_sql, db_name)
    
    def save_results(self, results: dict, output_file: str):
        save_evaluation_results(results, output_file)
