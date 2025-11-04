"""
LangGraph-based multi-agent orchestrator.
"""
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama
import structlog

logger = structlog.get_logger()


class AgentState(TypedDict):
    """State for agent orchestration."""
    user_id: int
    user_data: Dict[str, Any]
    financial_planner_result: Dict[str, Any]
    risk_assessment_result: Dict[str, Any]
    learning_result: Dict[str, Any]
    notification_result: Dict[str, Any]
    final_recommendations: Dict[str, Any]


class AgentOrchestrator:
    """Orchestrates multiple agents using LangGraph."""
    
    def __init__(self, llm: Ollama):
        """Initialize orchestrator."""
        self.llm = llm
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the agent orchestration graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("financial_planner", self._financial_planner_node)
        workflow.add_node("risk_assessment", self._risk_assessment_node)
        workflow.add_node("learning", self._learning_node)
        workflow.add_node("notification", self._notification_node)
        workflow.add_node("aggregate", self._aggregate_node)
        
        # Set entry point
        workflow.set_entry_point("financial_planner")
        
        # Define edges
        workflow.add_edge("financial_planner", "risk_assessment")
        workflow.add_edge("risk_assessment", "learning")
        workflow.add_edge("learning", "notification")
        workflow.add_edge("notification", "aggregate")
        workflow.add_edge("aggregate", END)
        
        return workflow.compile()
    
    def _financial_planner_node(self, state: AgentState) -> AgentState:
        """Financial Planner Agent node."""
        logger.info("Running Financial Planner Agent", user_id=state["user_id"])
        
        # This would call the actual agent service
        # For now, return mock result
        state["financial_planner_result"] = {
            "recommendations": [],
            "total_recommended_budget": 0,
            "savings_suggestion": 0,
            "insights": []
        }
        return state
    
    def _risk_assessment_node(self, state: AgentState) -> AgentState:
        """Risk Assessment Agent node."""
        logger.info("Running Risk Assessment Agent", user_id=state["user_id"])
        
        state["risk_assessment_result"] = {
            "risk_score": 0.5,
            "risk_level": "medium",
            "recommendations": [],
            "suitable_investment_types": []
        }
        return state
    
    def _learning_node(self, state: AgentState) -> AgentState:
        """Learning & Motivation Agent node."""
        logger.info("Running Learning Agent", user_id=state["user_id"])
        
        state["learning_result"] = {
            "quote": "Financial freedom is a journey, not a destination.",
            "tip": "Start small, stay consistent.",
            "progress_insights": []
        }
        return state
    
    def _notification_node(self, state: AgentState) -> AgentState:
        """Notification Agent node."""
        logger.info("Running Notification Agent", user_id=state["user_id"])
        
        state["notification_result"] = {
            "alerts": []
        }
        return state
    
    def _aggregate_node(self, state: AgentState) -> AgentState:
        """Aggregate results from all agents."""
        logger.info("Aggregating agent results", user_id=state["user_id"])
        
        state["final_recommendations"] = {
            "financial_plan": state["financial_planner_result"],
            "risk_assessment": state["risk_assessment_result"],
            "motivation": state["learning_result"],
            "alerts": state["notification_result"]["alerts"]
        }
        return state
    
    async def run(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent orchestration."""
        initial_state = AgentState(
            user_id=user_id,
            user_data=user_data,
            financial_planner_result={},
            risk_assessment_result={},
            learning_result={},
            notification_result={},
            final_recommendations={}
        )
        
        result = await self.graph.ainvoke(initial_state)
        return result["final_recommendations"]

