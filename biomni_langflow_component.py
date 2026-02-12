"""
Custom Langflow component for Biomni API
"""
from langflow import CustomComponent
from langflow.field_typing import Text
import requests
import json


class BiomniComponent(CustomComponent):
    display_name = "Biomni Assistant"
    description = "Interface to Biomni biomedical research AI assistant"
    
    def build_config(self):
        return {
            "api_url": {
                "display_name": "API URL",
                "type": "str",
                "value": "http://alan:8009",
                "info": "Base URL for Biomni API server"
            },
            "use_chat_history": {
                "display_name": "Use Chat History",
                "type": "bool",
                "value": False,
                "info": "Whether to maintain conversation history"
            },
            "timeout": {
                "display_name": "Timeout (seconds)",
                "type": "int", 
                "value": 180,  # Biomni can be slower, so higher timeout
                "info": "Request timeout (Biomni can take time for complex queries)"
            },
            "include_log": {
                "display_name": "Include Execution Log",
                "type": "bool",
                "value": False,
                "info": "Whether to include Biomni's execution log in the response"
            },
            "max_output_length": {
                "display_name": "Max Output Length",
                "type": "int",
                "value": 0,  # 0 means no limit
                "info": "Maximum characters to return (0 = no limit, useful for very long responses)"
            }
        }

    def build_inputs(self):
        return {
            "user_input": {
                "display_name": "User Query",
                "type": "str",
                "multiline": True,
                "info": "Biomedical question or research task for Biomni"
            }
        }

    def build(
        self,
        api_url: str,
        user_input: str,
        use_chat_history: bool = False,
        timeout: int = 180,
        include_log: bool = False,
        max_output_length: int = 0,
        **kwargs
    ) -> str:  # Change return type to str instead of Text
        
        # Handle both string and Message inputs
        if hasattr(user_input, 'text'):
            query_text = user_input.text
        else:
            query_text = str(user_input)
        
        # Set status to show processing
        self.status = "🧬 Processing Biomni query..."
        
        try:
            # Prepare the request
            if use_chat_history and hasattr(self, '_chat_history'):
                # Multi-turn conversation
                self._chat_history.append({"role": "user", "content": query_text})
                payload = {"messages": self._chat_history}
            else:
                # Single turn
                payload = {"prompt": query_text}
                if use_chat_history:
                    self._chat_history = [{"role": "user", "content": query_text}]
            
            # Update status to show API call
            self.status = "🌐 Calling Biomni API..."
            
            # Make API request
            response = requests.post(
                f"{api_url}/chat",
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Update status to show processing response
            self.status = "📊 Processing Biomni analysis..."
            
            if response.status_code == 200:
                result = response.json()
                assistant_reply = result.get("response", "No response received")
                
                # Update chat history if enabled
                if use_chat_history:
                    if not hasattr(self, '_chat_history'):
                        self._chat_history = []
                    self._chat_history.append({"role": "assistant", "content": assistant_reply})
                
                # Include execution log if requested
                if include_log and result.get("log"):
                    assistant_reply += f"\n\n--- Execution Log ---\n{result['log']}"
                
                # Include structured data if available
                if result.get("data"):
                    assistant_reply += f"\n\n[Structured Data Available: {type(result['data']).__name__}]"
                
                # Add PDF link if available
                pdf_path = result.get("pdf_path")
                if pdf_path:
                    # Extract timestamp folder and PDF filename from the path
                    # pdf_path looks like: ./local_outputs/20241002_174708_123/conversation_20241002_174708_123.pdf
                    import os
                    pdf_filename = os.path.basename(pdf_path)
                    timestamp_folder = os.path.basename(os.path.dirname(pdf_path))
                    
                    # Generate URL using the existing HTTP server at port 8100
                    pdf_url = f"http://alan:8100/{timestamp_folder}/{pdf_filename}"
                    
                    assistant_reply += f"\n\n📄 **Conversation Report**: [View PDF Analysis]({pdf_url})"
                    assistant_reply += f"\n\n*Click the link above to view the detailed analysis report with visualizations and complete execution steps.*"
                
                # Handle output length limit
                if max_output_length > 0 and len(assistant_reply) > max_output_length:
                    truncated_reply = assistant_reply[:max_output_length]
                    # Try to cut at a sentence boundary
                    last_period = truncated_reply.rfind('.')
                    if last_period > max_output_length * 0.8:  # If we find a period in the last 20%
                        truncated_reply = truncated_reply[:last_period + 1]
                    assistant_reply = truncated_reply + f"\n\n[Response truncated at {max_output_length} characters. Full response available in logs.]"
                
                # Set success status
                self.status = "✅ Biomni analysis completed successfully"
                
                # Ensure we return the full response as string
                return str(assistant_reply)
            else:
                error_msg = f"Error: API returned status {response.status_code}: {response.text}"
                self.status = f"❌ Biomni API error: {response.status_code}"
                return error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Error: Request timed out after {timeout} seconds. Biomni queries can take time - try increasing timeout or simplifying the query."
            self.status = f"⏰ Biomni timeout after {timeout}s"
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"Error: Could not connect to Biomni API at {api_url}. Is the server running?"
            self.status = "🔌 Biomni connection error"
            return error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.status = f"💥 Biomni error: {str(e)[:50]}..."
            return error_msg


# For OpenAI-compatible usage
class BiomniOpenAIComponent(CustomComponent):
    display_name = "Biomni (OpenAI Compatible)"
    description = "Biomni assistant using OpenAI-compatible endpoint"
    
    def build_config(self):
        return {
            "api_url": {
                "display_name": "API URL", 
                "type": "str",
                "value": "http://alan:8009/v1",
                "info": "OpenAI-compatible endpoint URL"
            },
            "timeout": {
                "display_name": "Timeout (seconds)",
                "type": "int",
                "value": 180  # Higher timeout for Biomni
            }
        }
    
    def build_inputs(self):
        return {
            "messages": {
                "display_name": "Messages",
                "type": "list",
                "info": "Chat messages in OpenAI format"
            }
        }
    
    def build(self, api_url: str, messages: list, timeout: int = 180, **kwargs) -> Text:
        try:
            payload = {
                "messages": messages,
                "model": "biomni"
            }
            
            response = requests.post(
                f"{api_url}/chat/completions",
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error: {str(e)}"


# Specialized components for different Biomni use cases
class BiomniLiteratureSearchComponent(CustomComponent):
    display_name = "Biomni Literature Search"
    description = "Specialized component for literature search and analysis"
    
    def build_config(self):
        return {
            "api_url": {
                "display_name": "API URL",
                "type": "str",
                "value": "http://alan:8009",
                "info": "Base URL for Biomni API server"
            },
            "timeout": {
                "display_name": "Timeout (seconds)",
                "type": "int", 
                "value": 300,  # Even higher for literature searches
                "info": "Request timeout for literature search"
            }
        }

    def build_inputs(self):
        return {
            "research_query": {
                "display_name": "Research Query",
                "type": "str",
                "multiline": True,
                "info": "Research question for literature search (e.g., 'What are the latest treatments for diabetes?')"
            }
        }

    def build(
        self,
        api_url: str,
        research_query: str,
        timeout: int = 300,
        **kwargs
    ) -> Text:
        
        # Format the query for literature search
        formatted_query = f"Search the literature and provide a comprehensive analysis: {research_query}"
        
        try:
            payload = {"prompt": formatted_query}
            
            response = requests.post(
                f"{api_url}/chat",
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response received")
            else:
                return f"Error: API returned status {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return f"Error: Literature search timed out after {timeout} seconds. Try a more specific query."
        except Exception as e:
            return f"Error: {str(e)}"