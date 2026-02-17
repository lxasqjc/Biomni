"""
Custom Langflow component for Biomni API
"""
from lfx.custom.custom_component.component import Component
from lfx.io import MultilineInput, Output, StrInput, MultilineInput, BoolInput, IntInput
from lfx.schema.message import Message

import requests


class BiomniComponent(Component):
    display_name = "Biomni Assistant"
    description = "Interface to Biomni biomedical research AI assistant"
    name = "Biomni Component"

    inputs = [
        StrInput(name="api_url", display_name="API URL", required=True),
        MultilineInput(name="model", display_name="Model", required=True),
        MultilineInput(name="temperature", display_name="temperature", required=True),
        MultilineInput(name="top_p", display_name="Top_P", required=True),
        MultilineInput(name="max_tokens", display_name="max_tokens", required=True),
        StrInput(name="n", display_name="n", required=True),
        IntInput(name="timeout", display_name="Timeout (seconds)", required=True, value=180),
        BoolInput(name="use_chat_history", display_name="Use Chat History", required=True),
        BoolInput(name="include_log", display_name="Include Execution Log", required=True),
        IntInput(name="max_output_length", display_name="Max Output Length", required=True, value=0),
        MultilineInput(name="user_input", display_name="User Query", required=True),
    ]

    outputs = [
        Output(display_name="Output Text", name="text", method="response"),
    ]

    def response(self) -> Message:
        # Handle both string and Message inputs
        if hasattr(self.user_input, 'text'):
            query_text = self.user_input.text
        else:
            query_text = str(self.user_input)

        
        # Set status to show processing
        self.status = "🧬 Processing Biomni query..."
        
        try:
            # Prepare the request
            if self.use_chat_history and hasattr(self, '_chat_history'):
                # Multi-turn conversation
                self._chat_history.append({"role": "user", "content": query_text})
                payload = {"messages": self._chat_history}
            else:
                # Single turn
                payload = {
                    "model": self.model,
                    "prompt": self.user_input,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "max_tokens": self.max_tokens,
                    "n": self.n,
                    "logprobs": True,
                    "top_logprobs": 20,
                    "stream": False
                }
                if self.use_chat_history:
                    self._chat_history = [{"role": "user", "content": query_text}]
            
            # Update status to show API call
            self.status = "🌐 Calling Biomni API..."
            
            # Make API request
            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Update status to show processing response
            self.status = "📊 Processing Biomni analysis..."
            
            if response.status_code == 200:
                result = response.json()
                assistant_reply = result.get("response", "No response received")
                
                # Store logprobs if returned by Biomni API
                logprobs_data = result.get("logprobs", None)
                if logprobs_data:
                    self._logprobs = logprobs_data
                
                # Update chat history if enabled
                if self.use_chat_history:
                    if not hasattr(self, '_chat_history'):
                        self._chat_history = []
                    self._chat_history.append({"role": "assistant", "content": assistant_reply})
                
                # Include execution log if requested
                if self.include_log and result.get("log"):
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
                    pdf_url = f"http://alan.astrazeneca.net:8100/{timestamp_folder}/{pdf_filename}"
                    
                    assistant_reply += f"\n\n📄 **Conversation Report**: [View PDF Analysis]({pdf_url})"
                    assistant_reply += f"\n\n*Click the link above to view the detailed analysis report with visualizations and complete execution steps.*"
                
                # Handle output length limit
                if self.max_output_length > 0 and len(assistant_reply) > self.max_output_length:
                    truncated_reply = assistant_reply[:self.max_output_length]
                    # Try to cut at a sentence boundary
                    last_period = truncated_reply.rfind('.')
                    if last_period > self.max_output_length * 0.8:  # If we find a period in the last 20%
                        truncated_reply = truncated_reply[:last_period + 1]
                    assistant_reply = truncated_reply + f"\n\n[Response truncated at {self.max_output_length} characters. Full response available in logs.]"
                
                # Set success status
                self.status = "✅ Biomni analysis completed successfully"
                
                # Ensure we return the full response as string
                return str(assistant_reply)
            else:
                error_msg = f"Error: API returned status {response.status_code}: {response.text}"
                self.status = f"❌ Biomni API error: {response.status_code}"
                return error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Error: Request timed out after {self.timeout} seconds. Biomni queries can take time - try increasing timeout or simplifying the query."
            self.status = f"⏰ Biomni timeout after {self.timeout}s"
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"Error: Could not connect to Biomni API at {self.api_url}. Is the server running?"
            self.status = "🔌 Biomni connection error"
            return error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.status = f"💥 Biomni error: {str(e)[:50]}..."
            return error_msg
        
        
        