from openai import AzureOpenAI
from typing import List, Dict, Any
from ..config.settings import AZURE_OPENAI_DEPLOYMENT, TEMPERATURE

class LLMClient:
    #Azure OpenAI client
    
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.deployment = AZURE_OPENAI_DEPLOYMENT
        self.temperature = TEMPERATURE
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Get chat completion from Azure OpenAI"""
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', None),
            top_p=kwargs.get('top_p', None),
        )
        return response.choices[0].message.content
    
    def simple_prompt(self, prompt: str, **kwargs) -> str:
        """Simple single-turn prompt"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, **kwargs)
    
    def conversation(self, conversation_history: List[Dict[str, str]], **kwargs) -> str:
        """Continue a conversation with history"""
        return self.chat_completion(conversation_history, **kwargs)

def create_llm_client(openai_client: AzureOpenAI) -> LLMClient:
    """Factory function to create LLM client"""
    return LLMClient(openai_client)
