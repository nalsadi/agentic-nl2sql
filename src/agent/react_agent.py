import re
from typing import Dict, List, Optional, Any
from ..prompts.system_prompt import get_react_prompt
from ..tools.database import db_manager, sql_query
from ..tools.sql_optimizer import (
    post_process_sql_for_accuracy, 
    optimize_for_database,
    clean_sql_formatting,
    validate_sql_syntax
)
from .llm_client import LLMClient
from ..config.settings import MAX_ITERATIONS

class ReactAgent:
    """ReAct pattern agent for SQL query generation and execution"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.tools = {
            "SQLQuery": sql_query
        }
        self.max_iterations = MAX_ITERATIONS
    
    def run(self, question: str, db_name: Optional[str] = None, return_full_conversation: bool = False) -> Any:
        """Run the ReAct agent to answer a question"""
        
        # Set database if provided
        if db_name:
            set_result = db_manager.set_database(db_name)
            print(f" {set_result}")
        
        history = []
        current_prompt = get_react_prompt(question)
        full_conversation = []
        
        for iteration in range(self.max_iterations):
            full_prompt = current_prompt + "\n" + "\n".join(history)
            reply = self.llm_client.simple_prompt(full_prompt)
            
            print(f"\n AGENT THINKING (Iteration {iteration + 1}):\n{reply}")
            full_conversation.append(f"Iteration {iteration + 1}:\n{reply}")
            
            # Check for final answer
            if "Answer:" in reply:
                answer = reply.split("Answer:")[-1].strip()
                print("\n Final Answer:", answer)
                
                if return_full_conversation:
                    return {
                        "answer": answer,
                        "full_conversation": "\n\n".join(full_conversation),
                        "history": history
                    }
                else:
                    return answer
            
            # Check if LLM is trying to write fake observations
            if "Observation:" in reply:
                print(" Agent tried to write fake observation. Stopping to prevent hallucination.")
                print("🔧 Reminding agent to only use real tool results...")
                history.append(reply.strip())
                history.append("SYSTEM: You wrote a fake observation. Only use real SQL tool results. Continue with another Action if needed.")
                continue
            
            # Extract latest Action + Input
            action_match = re.search(r"Action: (.+?)\nAction Input: (.+?)(?=\n\n|\nObservation:|\nAnswer:|\Z)", reply, re.DOTALL)
            if not action_match:
                print(" No valid action found. Exiting.")
                break
            
            tool = action_match.group(1).strip()
            tool_input = action_match.group(2).strip()
            
            # Clean up SQL code blocks if present
            tool_input = clean_sql_formatting(tool_input)
            
            # Validate SQL syntax
            is_valid, validation_msg = validate_sql_syntax(tool_input)
            if not is_valid:
                print(f" SQL validation warning: {validation_msg}")
            
            if tool not in self.tools:
                print(f" Unknown tool: {tool}")
                break
            
            print(f"\n Running Tool [{tool}] with input: {tool_input}")
            result = self.tools[tool](tool_input)
            print(f" Observation: {result}")
            
            # Add to memory
            history.append(reply.strip())
            history.append(f"Observation: {result}")
            full_conversation.append(f"Tool Result: {result}")
        
        print("Maximum iterations reached. Exiting.")
        final_answer = "I'm not sure - couldn't complete the analysis within the allowed iterations."
        
        if return_full_conversation:
            return {
                "answer": final_answer,
                "full_conversation": "\n\n".join(full_conversation),
                "history": history
            }
        else:
            return final_answer
    
    def run_enhanced(self, question: str, db_name: Optional[str] = None, return_full_conversation: bool = False) -> Any:
        """Enhanced agent with post-processing for better accuracy"""
        result = self.run(question, db_name, return_full_conversation)
        
        if return_full_conversation and isinstance(result, dict):
            # Extract the last SQL query from conversation
            conversation = result['full_conversation']
            
            # Find the last Action Input
            action_inputs = re.findall(r'Action Input:\s*(.*?)(?:\n|$)', conversation, re.IGNORECASE)
            if action_inputs:
                last_sql = action_inputs[-1].strip()
                if last_sql.upper().startswith('SELECT'):
                    # Post-process the SQL
                    improved_sql = post_process_sql_for_accuracy(last_sql, question)
                    
                    # Apply database-specific optimizations
                    if db_name:
                        improved_sql = optimize_for_database(improved_sql, db_name, question)
                    
                    if improved_sql != last_sql:
                        print(f"Post-processed SQL: {improved_sql}")
                        
                        # Try the improved query
                        try:
                            if db_name:
                                db_manager.set_database(db_name)
                            improved_result = sql_query(improved_sql)
                            print(f"Improved Result: {improved_result}")
                            
                            # Update the conversation with the improved result
                            result['improved_sql'] = improved_sql
                            result['improved_result'] = improved_result
                        except Exception as e:
                            print(f"Post-processing failed: {e}")
        
        return result
