"""
Agent for L3 (Tool-Augmented RAG) and L4 (Multi-turn Memory)
Orchestrates tool selection, execution, and conversation memory
"""

import json
import re
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from rag_pipeline import L1Retriever, L2Retriever, MockLLM, BedrockLLM
from tools import db_tool, api_tool
from config import MODE, AWS_ENABLED, MEMORY_MAX_TURNS
from logger import logger


class ConversationMemory:
    """L4: Store and retrieve conversation context"""

    def __init__(self, max_turns: int = MEMORY_MAX_TURNS):
        self.max_turns = max_turns
        self.messages: List[Dict] = []
        self.entities: Dict[str, Any] = {}

    def add_message(self, role: str, content: str):
        """Add a message to the history for Converse API"""
        self.messages.append({"role": role, "content": [{"text": content}]})
        # Keep only the last N turns (2 messages per turn: user and assistant)
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-(self.max_turns * 2):]

    def add_tool_use_message(self, message: Dict):
        """Add a message containing tool use"""
        self.messages.append(message)

    def get_messages(self) -> List[Dict]:
        """Return message history for Converse API"""
        return self.messages

    def clear(self):
        """Clear conversation history"""
        self.messages = []
        self.entities.clear()
        logger.info("Memory cleared")

    def resolve_pronoun(self, pronoun: str, context: str = "") -> Optional[str]:
        """Resolve pronouns (that service, their team, etc.) to actual entities"""
        # (Simplified implementation for now)
        return None


class L3Agent:
    """
    L3-L4 Agent: Combines RAG retrieval with tool orchestration and memory
    """

    def __init__(self):
        # Initialize retrievers (L1-L2)
        self.l1_retriever = L1Retriever()
        self.l2_retriever = L2Retriever()

        # Initialize LLM
        if MODE == "mock" or not AWS_ENABLED:
            self.llm = MockLLM()
        else:
            try:
                self.llm = BedrockLLM()
            except:
                self.llm = MockLLM()

        # Initialize memory (L4)
        self.memory = ConversationMemory()

        # Tool registry
        self.tools_map = self._register_tools()
        self.tool_config = self._get_tool_config()

        logger.info("L3 Agent initialized with Bedrock Converse API support")

    def _register_tools(self) -> Dict[str, callable]:
        """Register available tools"""
        return {
            "get_service_cost": db_tool.get_service_cost,
            "get_incidents": db_tool.get_incidents,
            "get_sla_targets": db_tool.get_sla_targets,
            "get_daily_metrics": db_tool.get_daily_metrics,
            "database_query": db_tool.query,
            "get_metrics": api_tool.get_metrics,
            "get_status": api_tool.get_status,
            "get_services": api_tool.get_services,
            "compare_services": api_tool.compare_services,
        }

    def _get_tool_config(self) -> Dict[str, Any]:
        """Define tool specifications for Bedrock Converse API"""
        return {
            'tools': [
                {
                    'toolSpec': {
                        'name': 'get_service_cost',
                        'description': 'Get historical cost data for a service by month.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'service_name': {'type': 'string', 'description': 'The service name (e.g., PaymentGW)'},
                                    'month': {'type': 'string', 'description': 'The month in YYYY-MM format (e.g., 2026-01)'}
                                },
                                'required': ['service_name']
                            }
                        }
                    }
                },
                {
                    'toolSpec': {
                        'name': 'get_incidents',
                        'description': 'Get list of incidents for a specific service.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'service_name': {'type': 'string', 'description': 'The service name'}
                                },
                                'required': ['service_name']
                            }
                        }
                    }
                },
                {
                    'toolSpec': {
                        'name': 'get_metrics',
                        'description': 'Get real-time metrics (latency, error rate, RPM) for a service.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'service_name': {'type': 'string', 'description': 'The service name'}
                                },
                                'required': ['service_name']
                            }
                        }
                    }
                },
                {
                    'toolSpec': {
                        'name': 'get_status',
                        'description': 'Get current health status and version for a service.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'service_name': {'type': 'string', 'description': 'The service name'}
                                },
                                'required': ['service_name']
                            }
                        }
                    }
                },
                {
                    'toolSpec': {
                        'name': 'get_sla_targets',
                        'description': 'Get SLA targets (latency, error rate, availability) for a service.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'service_name': {'type': 'string', 'description': 'The service name'}
                                },
                                'required': ['service_name']
                            }
                        }
                    }
                },
                {
                    'toolSpec': {
                        'name': 'get_daily_metrics',
                        'description': 'Get historical daily metrics for a service in a date range.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'service': {'type': 'string', 'description': 'The service name'},
                                    'start_date': {'type': 'string', 'description': 'Start date (YYYY-MM-DD)'},
                                    'end_date': {'type': 'string', 'description': 'End date (YYYY-MM-DD)'}
                                },
                                'required': ['service', 'start_date', 'end_date']
                            }
                        }
                    }
                },
                {
                    'toolSpec': {
                        'name': 'database_query',
                        'description': 'Execute a custom SQL query against the GeekBrain database. Use for complex costs, SLAs, or daily metrics analysis.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'sql_query': {'type': 'string', 'description': 'The SQL query to execute'}
                                },
                                'required': ['sql_query']
                            }
                        }
                    }
                },
                {
                    'toolSpec': {
                        'name': 'compare_services',
                        'description': 'Compare a specific metric (e.g., latency_ms, error_rate_percent) across multiple services.',
                        'inputSchema': {
                            'json': {
                                'type': 'object',
                                'properties': {
                                    'service_names': {
                                        'type': 'array', 
                                        'items': {'type': 'string'},
                                        'description': 'List of service names to compare'
                                    },
                                    'metric_name': {
                                        'type': 'string', 
                                        'description': 'The metric to compare (e.g., latency_ms)'
                                    }
                                },
                                'required': ['service_names', 'metric_name']
                            }
                        }
                    }
                }
            ]
        }

    def _decide_tool_use(self, question: str) -> Tuple[bool, List[str]]:
        """
        Decide if tools are needed and which ones
        Returns: (needs_tools, tool_names_to_use)
        """
        question_lower = question.lower()

        # Keywords that suggest tool use needed
        cost_keywords = ["cost", "expense", "price", "budget", "q1", "q2", "q3", "q4", "january", "february", "march"]
        metric_keywords = ["latency", "error", "uptime", "availability", "p99", "rpm", "current", "live", "now"]
        incident_keywords = ["incident", "issue", "problem", "outage", "downtime"]
        sla_keywords = ["sla", "target", "should", "should be", "within"]

        tools_needed = []

        # Detect if question requires database queries
        if any(kw in question_lower for kw in cost_keywords + incident_keywords + sla_keywords):
            tools_needed.append("database_query")

        # Detect if question requires current metrics
        if any(kw in question_lower for kw in metric_keywords):
            tools_needed.append("get_metrics")

        # Check if it's asking about specific services
        services = ["paymentgw", "ordersvc", "authsvc", "notificationsvc", "reportingsvc", "frauddetector"]
        for service in services:
            if service in question_lower:
                if not tools_needed:
                    tools_needed.append("get_metrics")
                break

        needs_tools = len(tools_needed) > 0

        logger.info(f"Tool decision: needs_tools={needs_tools}, tools={tools_needed}")

        return needs_tools, tools_needed

    def _extract_entities(self, answer: str, question: str) -> Dict[str, Any]:
        """Extract named entities from question and answer"""
        entities = {}

        # Extract service names
        services = ["PaymentGW", "OrderSvc", "AuthSvc", "NotificationSvc", "ReportingSvc", "FraudDetector"]
        for service in services:
            if service.lower() in (question + answer).lower():
                entities["service"] = service
                break

        # Extract team names
        teams = ["Platform", "Commerce", "Data", "Engagement"]
        for team in teams:
            if team.lower() in (question + answer).lower():
                entities["team"] = f"Team {team}"
                break

        # Extract dates
        import re
        date_pattern = r"(20\d{2}-\d{2}-\d{2}|january|february|march|q1|q2|2026)"
        dates = re.findall(date_pattern, question + answer, re.IGNORECASE)
        if dates:
            entities["date"] = dates[0]

        return entities

    def process_query(self, question: str, level: str = "auto") -> Dict[str, Any]:
        """
        Process a question through the agent pipeline.
        
        Args:
            question: User's question
            level: "l1" (simple RAG), "l2" (multi-doc), "l3" (with tools), "auto" (decide based on question)
        
        Returns:
            Dict with answer, sources, reasoning, etc.
        """
        logger.info(f"Agent processing: {question}")
        start_time = time.time()

        # Get conversation context (L4)
        conv_messages = self.memory.get_messages()

        # Decide level if auto
        if level == "auto":
            # For auto-detection, we'll try L3/L4 by default if in cloud mode
            level = "l3" if MODE == "cloud" else "l2"

        logger.info(f"Processing at level: {level}")

        # Route to appropriate level
        if level == "l1":
            result = self.l1_retriever.answer_question(question)
        elif level == "l2":
            result = self.l2_retriever.answer_question(question)
        elif level == "l3":
            result = self._process_l3(question, conv_messages)
        else:
            result = {"error": f"Unknown level: {level}"}

        # Update memory (L4)
        if "messages" in result:
            # Full message history from L3 process
            self.memory.messages = result["messages"]
        else:
            # Manual update for L1/L2
            self.memory.add_message("user", question)
            self.memory.add_message("assistant", result.get("answer", ""))

        # Add duration
        duration = time.time() - start_time
        result["duration_seconds"] = duration

        logger.info(f"Query processed in {duration:.2f}s")
        return result

    def _process_l3(self, question: str, conv_messages: List[Dict]) -> Dict[str, Any]:
        """L3-L4: Orchestrate tool use and RAG with Bedrock Converse"""
        logger.info("L3: Starting multi-turn tool-augmented retrieval")
        
        # Add current question to messages
        messages = list(conv_messages)
        messages.append({"role": "user", "content": [{"text": question}]})
        
        # Initial retrieval from KB for background context
        chunks = self.l2_retriever.retrieve_chunks(question, top_k=5)
        kb_context = "\n\n".join([f"[Source: {c['source']}]\n{c['content']}" for c in chunks])
        
        system_prompt = f"""You are an expert assistant for GeekBrain fintech startup.
You have access to historical data (Database) and real-time data (Monitoring API).
Use the tools provided to answer technical and financial questions.

Knowledge Base Context (Policy/Architecture):
{kb_context}

Rules:
1. If asked about metrics (latency, error rate), use get_metrics.
2. If asked about costs or incidents, use database tools.
3. If asked about SLA targets or historical thresholds, use get_sla_targets from the database.
4. If the knowledge base context has the answer, you can use it directly.
5. Always cite your sources (tool data or document name).
6. If a service name is mentioned but ambiguous, try to match it to: PaymentGW, OrderSvc, AuthSvc, NotificationSvc, ReportingSvc, FraudDetector.
7. Important: For SLA compliance questions, ALWAYS check current metrics AND SLA targets from tools. Do not rely solely on KB text if tools are available."""

        try:
            # Bedrock Converse API Loop (handles tool usage)
            client = self.llm.client
            model_id = self.llm.model_id
            
            response = client.converse(
                modelId=model_id,
                system=[{"text": system_prompt}],
                messages=messages,
                toolConfig=self.tool_config
            )
            
            output_msg = response['output']['message']
            messages.append(output_msg)
            
            tools_called = []
            
            # Check if model wants to use tools
            while 'toolUse' in [part.keys() for part in output_msg['content'] if isinstance(part, dict)][0] or any('toolUse' in part for part in output_msg['content']):
                tool_results_content = []
                
                for content_part in output_msg['content']:
                    if 'toolUse' in content_part:
                        tool_use = content_part['toolUse']
                        tool_name = tool_use['name']
                        tool_input = tool_use['input']
                        tool_id = tool_use['toolUseId']
                        
                        logger.info(f"Agent wants to use tool: {tool_name} with input: {tool_input}")
                        tools_called.append(tool_name)
                        
                        if tool_name in self.tools_map:
                            try:
                                # Call the actual tool function
                                result = self.tools_map[tool_name](**tool_input)
                                tool_results_content.append({
                                    'toolResult': {
                                        'toolUseId': tool_id,
                                        'content': [{'json': result}],
                                        'status': 'success'
                                    }
                                })
                            except Exception as e:
                                tool_results_content.append({
                                    'toolResult': {
                                        'toolUseId': tool_id,
                                        'content': [{'text': str(e)}],
                                        'status': 'error'
                                    }
                                })
                
                if tool_results_content:
                    messages.append({
                        'role': 'user',
                        'content': tool_results_content
                    })
                    
                    # Call model again with tool results
                    response = client.converse(
                        modelId=model_id,
                        system=[{"text": system_prompt}],
                        messages=messages,
                        toolConfig=self.tool_config
                    )
                    output_msg = response['output']['message']
                    messages.append(output_msg)
                else:
                    break
            
            final_answer = ""
            for part in output_msg['content']:
                if 'text' in part:
                    final_answer += part['text']
            
            return {
                "answer": final_answer,
                "sources": [c["source"] for c in chunks],
                "tools_called": tools_called,
                "level": "L3/L4",
                "success": True,
                "messages": messages # For memory update
            }

        except Exception as e:
            logger.error(f"Error in _process_l3: {e}")
            return {
                "answer": f"I encountered an error while processing your request: {e}",
                "level": "L3/L4",
                "success": False
            }

    def _call_tool(self, tool_name: str, question: str) -> Any:
        """Call a tool with question context"""
        question_lower = question.lower()

        if tool_name == "database_query":
            # For now, return a generic message
            logger.info(f"Tool would execute: SELECT ... based on question")
            return {"query_executed": True, "note": "See tool_results for actual data"}

        elif tool_name == "get_service_cost":
            # Extract service name
            services = ["PaymentGW", "OrderSvc", "AuthSvc", "NotificationSvc", "ReportingSvc", "FraudDetector"]
            service = next((s for s in services if s.lower() in question_lower), "PaymentGW")
            return api_tool.get_metrics(service)

        elif tool_name == "get_metrics":
            services = ["PaymentGW", "OrderSvc", "AuthSvc", "NotificationSvc", "ReportingSvc", "FraudDetector"]
            service = next((s for s in services if s.lower() in question_lower), "PaymentGW")
            return api_tool.get_metrics(service)

        elif tool_name == "get_status":
            services = ["PaymentGW", "OrderSvc", "AuthSvc", "NotificationSvc", "ReportingSvc", "FraudDetector"]
            service = next((s for s in services if s.lower() in question_lower), "PaymentGW")
            return api_tool.get_status(service)

        else:
            return {"status": "tool not implemented in mock"}


# Global agent instance
agent = L3Agent()
