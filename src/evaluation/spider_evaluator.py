import json
import re
from typing import Dict, List, Any, Tuple
from ..agent.react_agent import ReactAgent
from ..tools.database import db_manager

def normalize_query_results(results: List[Dict]) -> List[Tuple]:
    """Normalize query results for comparison by converting to sorted tuples"""
    if not results:
        return []
    
    # Convert each row to a tuple of values, sorted by keys for consistency
    normalized = []
    for row in results:
        if isinstance(row, dict):
            # Sort by keys to ensure consistent ordering
            sorted_values = tuple(str(v) if v is not None else None for k, v in sorted(row.items()))
            normalized.append(sorted_values)
        else:
            # Handle case where row is already a tuple/list
            normalized.append(tuple(str(v) if v is not None else None for v in row))
    
    # Sort the results for comparison
    return sorted(normalized)

def compare_query_results(expected_query: str, agent_query: str, db_name: str) -> Dict[str, Any]:
    """Compare results from expected query vs agent query"""
    comparison = {
        "match": False,
        "expected_results": None,
        "agent_results": None,
        "expected_error": None,
        "agent_error": None,
        "details": ""
    }
    
    # Set the database
    db_manager.set_database(db_name)
    
    # Execute expected query
    try:
        expected_result_str = db_manager.execute_query(expected_query)
        if expected_result_str.startswith("Query executed successfully but returned no results"):
            comparison["expected_results"] = []
        elif expected_result_str.startswith(("Database error:", "Error executing query:")):
            comparison["expected_error"] = expected_result_str
            comparison["expected_results"] = None
        else:
            comparison["expected_results"] = json.loads(expected_result_str)
    except Exception as e:
        comparison["expected_error"] = f"Error executing expected query: {str(e)}"
        comparison["expected_results"] = None
    
    # Execute agent query
    try:
        agent_result_str = db_manager.execute_query(agent_query)
        if agent_result_str.startswith("Query executed successfully but returned no results"):
            comparison["agent_results"] = []
        elif agent_result_str.startswith(("Database error:", "Error executing query:")):
            comparison["agent_error"] = agent_result_str
            comparison["agent_results"] = None
        else:
            comparison["agent_results"] = json.loads(agent_result_str)
    except Exception as e:
        comparison["agent_error"] = f"Error executing agent query: {str(e)}"
        comparison["agent_results"] = None
    
    # Compare results if both queries executed successfully
    if comparison["expected_results"] is not None and comparison["agent_results"] is not None:
        expected_normalized = normalize_query_results(comparison["expected_results"])
        agent_normalized = normalize_query_results(comparison["agent_results"])
        
        comparison["match"] = expected_normalized == agent_normalized
        
        if comparison["match"]:
            comparison["details"] = "Results match perfectly"
        else:
            comparison["details"] = f"Results differ. Expected {len(expected_normalized)} rows, got {len(agent_normalized)} rows"
    
    elif comparison["expected_error"] and comparison["agent_error"]:
        # Both queries failed - could be considered a match if same error type
        comparison["match"] = False
        comparison["details"] = "Both queries failed"
    
    else:
        comparison["match"] = False
        if comparison["expected_error"]:
            comparison["details"] = f"Expected query failed: {comparison['expected_error']}"
        elif comparison["agent_error"]:
            comparison["details"] = f"Agent query failed: {comparison['agent_error']}"
        else:
            comparison["details"] = "One query succeeded, the other failed"
    
    return comparison

def extract_sql_from_agent_response(agent_response: str) -> str:
    """Extract the final SQL query from agent response or conversation"""
    if not agent_response or isinstance(agent_response, dict):
        return ""
    
    # Look for SQL queries in the response
    sql_patterns = [
        r'Action Input:\s*(SELECT[^;\n]*?)(?:\s*\n|$)',
        r'```sql\s*(SELECT.*?)\s*```',
        r'```\s*(SELECT.*?)\s*```',
        r'(SELECT[^;\n]*)',
    ]
    
    found_queries = []
    for pattern in sql_patterns:
        matches = re.findall(pattern, agent_response, re.IGNORECASE | re.DOTALL)
        for match in matches:
            cleaned_match = match.strip()
            # Remove any trailing observation text or newlines
            if 'Observation:' in cleaned_match:
                cleaned_match = cleaned_match.split('Observation:')[0].strip()
            if '\n' in cleaned_match and not cleaned_match.count('\n') > 2:
                cleaned_match = cleaned_match.split('\n')[0].strip()
            if cleaned_match and cleaned_match.upper().startswith('SELECT'):
                found_queries.append(cleaned_match)
    
    # Return the last (most recent) SQL query found
    if found_queries:
        return found_queries[-1]
    
    return ""

def load_spider_examples(file_path: str, limit: int = None) -> List[Dict]:
    """Load Spider examples from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if limit:
        return data[:limit]
    return data

def evaluate_agent_on_spider(agent: ReactAgent, examples: List[Dict], limit: int = 5) -> Dict:
    """Test the agent on Spider examples with result comparison"""
    results = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "correct_results": 0,
        "details": []
    }
    
    for i, example in enumerate(examples[:limit]):
        print(f"\n{'='*60}")
        print(f"TEST {i+1}/{min(limit, len(examples))}: {example['db_id']}")
        print(f"{'='*60}")
        print(f"Question: {example['question']}")
        print(f"Expected SQL: {example['query']}")
        
        try:
            # Run the agent with full conversation to extract SQL
            agent_result = agent.run(example['question'], example['db_id'], return_full_conversation=True)
            
            if isinstance(agent_result, dict):
                agent_answer = agent_result.get('answer', 'No answer')
                agent_conversation = agent_result.get('full_conversation', '')
            else:
                agent_answer = str(agent_result)
                agent_conversation = str(agent_result)
            
            # Extract the SQL query from agent response
            agent_sql = extract_sql_from_agent_response(agent_conversation)
            
            results["total"] += 1
            
            detail = {
                "db_id": example['db_id'],
                "question": example['question'],
                "expected_sql": example['query'],
                "agent_answer": agent_answer,
                "agent_sql": agent_sql,
                "status": "success"
            }
            
            # Compare query results if we have a valid SQL query
            if agent_sql and agent_sql.upper().startswith('SELECT'):
                try:
                    comparison = compare_query_results(example['query'], agent_sql, example['db_id'])
                    detail["result_comparison"] = comparison
                    
                    if comparison["match"]:
                        results["correct_results"] += 1
                        print(f"Results match! {comparison['details']}")
                        detail["result_status"] = "correct"
                    else:
                        print(f"Results don't match: {comparison['details']}")
                        detail["result_status"] = "incorrect"
                        
                        # Show comparison details
                        if comparison["expected_results"] is not None:
                            print(f"Expected results: {len(comparison['expected_results'])} rows")
                        if comparison["agent_results"] is not None:
                            print(f"Agent results: {len(comparison['agent_results'])} rows")
                
                except Exception as e:
                    print(f"Error comparing results: {str(e)}")
                    detail["result_status"] = "comparison_error"
                    detail["comparison_error"] = str(e)
            else:
                print("No valid SQL query found in agent response")
                detail["result_status"] = "no_sql"
            
            results["successful"] += 1
            results["details"].append(detail)
            
        except Exception as e:
            print(f"Error testing example: {str(e)}")
            results["total"] += 1
            results["failed"] += 1
            
            results["details"].append({
                "db_id": example['db_id'],
                "question": example['question'],
                "expected_sql": example['query'],
                "agent_answer": f"Error: {str(e)}",
                "status": "failed"
            })
    
    return results

def evaluate_enhanced_agent(agent: ReactAgent, examples: List[Dict], limit: int = 5) -> Dict:
    """Test the enhanced agent with post-processing and result comparison"""
    results = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "correct_results": 0,
        "improved_correct_results": 0,
        "details": []
    }
    
    for i, example in enumerate(examples[:limit]):
        print(f"\n{'='*60}")
        print(f"ENHANCED TEST {i+1}/{min(limit, len(examples))}: {example['db_id']}")
        print(f"{'='*60}")
        print(f"Question: {example['question']}")
        print(f"Expected SQL: {example['query']}")
        
        try:
            # Run the enhanced agent
            result = agent.run_enhanced(
                example['question'], 
                example['db_id'], 
                return_full_conversation=True
            )
            
            results["total"] += 1
            results["successful"] += 1
            
            detail = {
                "db_id": example['db_id'],
                "question": example['question'],
                "expected_sql": example['query'],
                "agent_answer": result.get('answer', 'No answer'),
                "full_conversation": result.get('full_conversation', ''),
                "status": "success"
            }
            
            # Extract original SQL from conversation
            agent_sql = extract_sql_from_agent_response(result.get('full_conversation', ''))
            detail["agent_sql"] = agent_sql
            
            # Compare original results if we have SQL
            if agent_sql and agent_sql.upper().startswith('SELECT'):
                try:
                    comparison = compare_query_results(example['query'], agent_sql, example['db_id'])
                    detail["result_comparison"] = comparison
                    
                    if comparison["match"]:
                        results["correct_results"] += 1
                        print(f"Original results match! {comparison['details']}")
                        detail["result_status"] = "correct"
                    else:
                        print(f"Original results don't match: {comparison['details']}")
                        detail["result_status"] = "incorrect"
                
                except Exception as e:
                    print(f"Error comparing original results: {str(e)}")
                    detail["result_status"] = "comparison_error"
                    detail["comparison_error"] = str(e)
            else:
                detail["result_status"] = "no_sql"
            
            # Check improved results if available
            if 'improved_sql' in result:
                detail['improved_sql'] = result['improved_sql']
                detail['improved_result'] = result['improved_result']
                
                try:
                    improved_comparison = compare_query_results(
                        example['query'], 
                        result['improved_sql'], 
                        example['db_id']
                    )
                    detail["improved_comparison"] = improved_comparison
                    
                    if improved_comparison["match"]:
                        results["improved_correct_results"] += 1
                        print(f"Improved results match! {improved_comparison['details']}")
                        detail["improved_status"] = "correct"
                    else:
                        print(f"Improved results don't match: {improved_comparison['details']}")
                        detail["improved_status"] = "incorrect"
                
                except Exception as e:
                    print(f"Error comparing improved results: {str(e)}")
                    detail["improved_status"] = "comparison_error"
            
            results["details"].append(detail)
            
        except Exception as e:
            print(f"Error testing example: {str(e)}")
            results["total"] += 1
            results["failed"] += 1
            
            results["details"].append({
                "db_id": example['db_id'],
                "question": example['question'],
                "expected_sql": example['query'],
                "agent_answer": f"Error: {str(e)}",
                "status": "failed"
            })
    
    return results

def test_single_query_comparison(expected_sql: str, agent_sql: str, db_name: str) -> Dict:
    """Test comparison between two queries for debugging purposes"""
    print(f"Testing query comparison on database: {db_name}")
    print(f"Expected SQL: {expected_sql}")
    print(f"Agent SQL: {agent_sql}")
    
    comparison = compare_query_results(expected_sql, agent_sql, db_name)
    
    print(f"\n Comparison Results:")
    print(f"Match: {comparison['match']}")
    print(f"Details: {comparison['details']}")
    
    if comparison['expected_results'] is not None:
        print(f"Expected results: {len(comparison['expected_results'])} rows")
        if len(comparison['expected_results']) <= 5:  # Show small result sets
            for i, row in enumerate(comparison['expected_results'][:3]):
                print(f"  Row {i+1}: {row}")
    
    if comparison['agent_results'] is not None:
        print(f"Agent results: {len(comparison['agent_results'])} rows")
        if len(comparison['agent_results']) <= 5:  # Show small result sets
            for i, row in enumerate(comparison['agent_results'][:3]):
                print(f"  Row {i+1}: {row}")
    
    if comparison['expected_error']:
        print(f"Expected query error: {comparison['expected_error']}")
    
    if comparison['agent_error']:
        print(f"Agent query error: {comparison['agent_error']}")
    
    return comparison

def print_evaluation_summary(results: Dict):
    """Print a summary of evaluation results with accuracy metrics"""
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['successful']/results['total']*100:.1f}%" if results['total'] > 0 else "No tests run")
    
    # Result accuracy metrics
    if 'correct_results' in results:
        print(f"Correct results: {results['correct_results']}")
        print(f"Result accuracy: {results['correct_results']/results['successful']*100:.1f}%" if results['successful'] > 0 else "No successful tests")
    
    if 'improved_correct_results' in results:
        print(f"Improved correct results: {results['improved_correct_results']}")
        improved_total = sum(1 for d in results['details'] if 'improved_sql' in d)
        if improved_total > 0:
            print(f"Improved accuracy: {results['improved_correct_results']/improved_total*100:.1f}%")
    
    # Print failed cases for analysis
    failed_cases = [d for d in results['details'] if d['status'] == 'failed']
    if failed_cases:
        print(f"\nFailed cases ({len(failed_cases)}):")
        for case in failed_cases:
            print(f"  - {case['db_id']}: {case['question'][:50]}...")
    
    # Print incorrect result cases
    incorrect_cases = [d for d in results['details'] if d.get('result_status') == 'incorrect']
    if incorrect_cases:
        print(f"\nIncorrect results ({len(incorrect_cases)}):")
        for case in incorrect_cases:
            print(f"  - {case['db_id']}: {case['question'][:50]}...")
            if 'result_comparison' in case:
                print(f"    Reason: {case['result_comparison'].get('details', 'Unknown')}")

    # Print summary by result status
    if results.get('details'):
        status_counts = {}
        for detail in results['details']:
            status = detail.get('result_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            print(f"\n Result status breakdown:")
            for status, count in status_counts.items():
                print(f"  - {status}: {count}")

def save_evaluation_results(results: Dict, output_file: str):
    """Save evaluation results to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")
