import os
import json
import re
import traceback
import requests
from typing import Generator, Dict, Any, List

# Import tools registry
from tools import TOOLS

SYSTEM_PROMPT = """You are a highly capable Agentic AI Chatbot. You solve the user's queries by thinking step-by-step and calling tools when necessary.

You have access to the following tools:
1. calculate(expression: str) -> str
   - Purpose: Safely evaluates a mathematical expression.
   - Example parameters: {"expression": "2 + 2 * 3"}
2. get_time() -> str
   - Purpose: Returns the current date and time.
   - Example parameters: {} (no arguments needed)
3. search_wikipedia(query: str) -> str
   - Purpose: Searches Wikipedia and returns a summary.
   - Example parameters: {"query": "Quantum Computing"}
4. get_weather(city: str) -> str
   - Purpose: Simulates weather information for a given city.
   - Example parameters: {"city": "Paris"}
5. plot_chart(chart_type: str, data: dict, x_label: str, y_label: str) -> str
   - Purpose: Generates and displays a line, bar, or area chart.
   - Example parameters: {"chart_type": "bar", "data": {"Month": ["Jan", "Feb", "Mar"], "Sales": [120, 150, 180]}, "x_label": "Month", "y_label": "Sales"}

To answer questions, you must follow a strict loop of Thought, Action, and Observation.
Use the following exact format:

Thought: Describe your reasoning about what to do next.
Action: {"tool_name": "name_of_tool", "parameters": {"param_name": "value"}}

Wait for the observation. Once you receive the observation, continue the loop:
Thought: Describe your next reasoning step.
Action: ... (or Final Answer)

If you have all the information to answer the user's question, output:
Thought: I now have the final answer.
Final Answer: The final response to the user.

CRITICAL RULES:
1. At each turn, you must output EITHER an 'Action:' block OR a 'Final Answer:' block, never both.
2. The Action block must be a single valid JSON object on the line following 'Action:'.
3. Do not make up tools. Only use the 4 tools listed above.
4. If the question can be answered from memory/general knowledge without tools, immediately output Thought and Final Answer.
"""

class ReActAgent:
    def __init__(self, provider: str = "groq", api_key: str = None):
        self.provider = provider.lower()
        if self.provider == "groq":
            self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        elif self.provider == "gemini":
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        elif self.provider == "nvidia":
            self.api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        else:
            self.api_key = api_key
            
        self.memory: List[Dict[str, str]] = []  # Keep the last 10 messages

    def add_to_memory(self, role: str, content: str):
        """Adds a message to memory and maintains a strict limit of 10 messages."""
        self.memory.append({"role": role, "content": content})
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]

    def clear_memory(self):
        """Clears the conversation memory."""
        self.memory = []

    def _stream_groq(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Streams responses from Groq API."""
        from groq import Groq
        if not self.api_key:
            raise ValueError("Groq API Key is not set.")
        
        client = Groq(api_key=self.api_key)
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        
        stream = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=full_messages,
            temperature=0.2,
            max_tokens=1024,
            top_p=1.0,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def _stream_gemini(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Streams responses from Gemini API."""
        import google.generativeai as genai
        if not self.api_key:
            raise ValueError("Gemini API Key is not set.")
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [msg["content"]]})
            
        response = model.generate_content(
            contents=contents,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
            stream=True
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _stream_nvidia(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Streams responses from NVIDIA NIM API using Llama 3.3 70B."""
        if not self.api_key:
            raise ValueError("NVIDIA API Key is not set.")
        
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        
        payload = {
            "model": "meta/llama-3.3-70b-instruct",
            "messages": full_messages,
            "temperature": 0.2,
            "max_tokens": 1024,
            "top_p": 1.0,
            "stream": True
        }
        
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"NVIDIA API Error (Status {response.status_code}): {response.text}")
            
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    data_content = line_str[6:]
                    if data_content == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_content)
                        delta = chunk_data["choices"][0]["delta"]
                        if "content" in delta:
                            yield delta["content"]
                    except:
                        pass

    def _call_llm_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Dispatches streaming LLM calls based on provider choice."""
        if self.provider == "groq":
            yield from self._stream_groq(messages)
        elif self.provider == "gemini":
            yield from self._stream_gemini(messages)
        elif self.provider == "nvidia":
            yield from self._stream_nvidia(messages)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def parse_llm_response(self, text: str) -> Dict[str, Any]:
        """Parses the LLM output into Thought, Action, or Final Answer."""
        # Find Thought
        thought_match = re.search(r"Thought:\s*(.*?)(?=(Action:|Final Answer:|$))", text, re.DOTALL | re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else ""
        
        # Check for Action
        action_match = re.search(r"Action:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
        if action_match:
            action_content = action_match.group(1).strip()
            # Clean markdown code formatting if any
            action_content = re.sub(r"^```json\s*", "", action_content, flags=re.IGNORECASE)
            action_content = re.sub(r"^```\s*", "", action_content)
            action_content = re.sub(r"\s*```$", "", action_content)
            action_content = action_content.strip()
            
            try:
                # Find the actual JSON substring inside
                json_match = re.search(r"\{.*\}", action_content, re.DOTALL)
                if json_match:
                    action_json = json.loads(json_match.group(0))
                    return {
                        "type": "action",
                        "thought": thought or "Using tool...",
                        "tool_name": action_json.get("tool_name"),
                        "parameters": action_json.get("parameters", {})
                    }
            except Exception as e:
                return {
                    "type": "error",
                    "thought": thought,
                    "error": f"Failed to parse action JSON: {str(e)}. Raw Action: '{action_content}'"
                }

        # Check for Final Answer
        final_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
        if final_match:
            final_answer = final_match.group(1).strip()
            return {
                "type": "final_answer",
                "thought": thought or "Delivering final answer.",
                "answer": final_answer
            }
            
        # Fallback: if LLM wrote something but it doesn't match ReAct format perfectly, treat it as Final Answer
        if text.strip():
            # Check if there is JSON inside anyway
            try:
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                if json_match:
                    action_json = json.loads(json_match.group(0))
                    if "tool_name" in action_json:
                        return {
                            "type": "action",
                            "thought": thought or "Using tool...",
                            "tool_name": action_json.get("tool_name"),
                            "parameters": action_json.get("parameters", {})
                        }
            except:
                pass
                
            return {
                "type": "final_answer",
                "thought": thought or "Formulating response.",
                "answer": text.strip()
            }
            
        return {
            "type": "error",
            "error": "Received empty response from the AI model."
        }

    def run(self, user_prompt: str) -> Generator[Dict[str, Any], None, None]:
        """Runs the ReAct loop and streams the steps dynamically."""
        # Initialize scratchpad for this turn
        scratchpad = [{"role": "user", "content": user_prompt}]
        max_loops = 5
        
        for loop_idx in range(max_loops):
            current_messages = self.memory + scratchpad
            full_response_text = ""
            
            # Yield thought start
            yield {
                "type": "thought_start",
                "step": loop_idx + 1
            }
            
            try:
                # Call LLM and stream tokens
                for token in self._call_llm_stream(current_messages):
                    full_response_text += token
                    
                    # Extract current thought content dynamically
                    thought_content = ""
                    thought_match = re.search(r"Thought:\s*(.*?)(?=(Action:|Final Answer:|$))", full_response_text, re.DOTALL | re.IGNORECASE)
                    if thought_match:
                        thought_content = thought_match.group(1).strip()
                    else:
                        clean_text = re.sub(r"^Thought:\s*", "", full_response_text, flags=re.IGNORECASE)
                        thought_content = clean_text.strip()
                    
                    yield {
                        "type": "thought_stream",
                        "step": loop_idx + 1,
                        "thought": thought_content
                    }
            except Exception as e:
                yield {
                    "type": "error",
                    "step": loop_idx + 1,
                    "error": f"API Error: {str(e)}"
                }
                return
                
            # Parse the full response
            parsed = self.parse_llm_response(full_response_text)
            
            if parsed["type"] == "error":
                yield {
                    "type": "error",
                    "step": loop_idx + 1,
                    "error": parsed["error"]
                }
                return
                
            # Yield the final static thought
            yield {
                "type": "thought",
                "step": loop_idx + 1,
                "thought": parsed["thought"],
                "raw_response": full_response_text
            }
            
            if parsed["type"] == "final_answer":
                # Save the final interaction to memory
                self.add_to_memory("user", user_prompt)
                self.add_to_memory("assistant", parsed["answer"])
                
                yield {
                    "type": "final_answer",
                    "step": loop_idx + 1,
                    "answer": parsed["answer"]
                }
                return
                
            if parsed["type"] == "action":
                tool_name = parsed["tool_name"]
                parameters = parsed["parameters"]
                
                yield {
                    "type": "action",
                    "step": loop_idx + 1,
                    "tool_name": tool_name,
                    "parameters": parameters
                }
                
                # Execute tool
                if tool_name not in TOOLS:
                    observation = f"Error: Tool '{tool_name}' is not recognized or available. Available tools are: {list(TOOLS.keys())}."
                else:
                    try:
                        tool_func = TOOLS[tool_name]
                        
                        if tool_name == "get_time":
                            observation = tool_func()
                        else:
                            if isinstance(parameters, dict):
                                # Map key if they sent a single-key dictionary with an incorrect key name
                                expected_keys = {
                                    "calculate": "expression",
                                    "search_wikipedia": "query",
                                    "get_weather": "city"
                                }
                                expected_key = expected_keys.get(tool_name)
                                if expected_key and expected_key not in parameters and len(parameters) == 1:
                                    val = list(parameters.values())[0]
                                    parameters = {expected_key: val}
                                
                                # Call with mapped arguments
                                observation = tool_func(**parameters)
                            else:
                                if tool_name == "calculate":
                                    observation = tool_func(expression=str(parameters))
                                elif tool_name == "search_wikipedia":
                                    observation = tool_func(query=str(parameters))
                                elif tool_name == "get_weather":
                                    observation = tool_func(city=str(parameters))
                                else:
                                    observation = f"Error: Invalid parameters format for tool '{tool_name}'."
                    except TypeError as te:
                        observation = f"Error calling tool '{tool_name}' with parameters {parameters}: {str(te)}. Please correct parameter name."
                    except Exception as e:
                        observation = f"Error executing tool '{tool_name}': {str(e)}"
                
                yield {
                    "type": "observation",
                    "step": loop_idx + 1,
                    "result": observation
                }
                
                scratchpad.append({"role": "assistant", "content": full_response_text})
                scratchpad.append({"role": "user", "content": f"Observation: {observation}"})
                
        # If we exceeded the loop limit
        yield {
            "type": "final_answer",
            "step": max_loops,
            "answer": "I apologize, but I could not arrive at a final answer within the maximum number of reasoning steps."
        }
