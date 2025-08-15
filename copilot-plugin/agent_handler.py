"""
Microsoft Copilot Agent Handler
Handles complex agent requests and workflows
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from fastapi import HTTPException

from plugin_handler import CopilotPluginHandler

logger = logging.getLogger(__name__)


class AgentWorkflow:
    """Workflow for complex agent operations"""
    
    def __init__(self, plugin_handler: CopilotPluginHandler):
        self.plugin_handler = plugin_handler
    
    async def execute_workflow(
        self, 
        access_token: str, 
        workflow_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute complex workflows
        
        Args:
            access_token: Azure AD access token
            workflow_type: Type of workflow
            parameters: Workflow parameters
            
        Returns:
            Workflow result
        """
        try:
            if workflow_type == "send_team_message":
                return await self._send_team_message_workflow(access_token, parameters)
            elif workflow_type == "create_team_report":
                return await self._create_team_report_workflow(access_token, parameters)
            elif workflow_type == "search_and_summarize":
                return await self._search_and_summarize_workflow(access_token, parameters)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
                
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")
    
    async def _send_team_message_workflow(
        self, 
        access_token: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message to team with validation"""
        try:
            team_name = parameters.get("team_name")
            channel_name = parameters.get("channel_name")
            message = parameters.get("message")
            
            # Step 1: Get user's teams
            teams = await self.plugin_handler.get_user_teams(access_token)
            
            # Step 2: Find target team
            target_team = None
            for team in teams:
                if team.get("display_name", "").lower() == team_name.lower():
                    target_team = team
                    break
            
            if not target_team:
                return {
                    "success": False,
                    "error": f"Team '{team_name}' not found",
                    "available_teams": [team.get("display_name") for team in teams]
                }
            
            # Step 3: Get team channels
            channels = await self.plugin_handler.get_team_channels(
                access_token, target_team["id"]
            )
            
            # Step 4: Find target channel
            target_channel = None
            for channel in channels:
                if channel.get("display_name", "").lower() == channel_name.lower():
                    target_channel = channel
                    break
            
            if not target_channel:
                return {
                    "success": False,
                    "error": f"Channel '{channel_name}' not found in team '{team_name}'",
                    "available_channels": [channel.get("display_name") for channel in channels]
                }
            
            # Step 5: Send message
            result = await self.plugin_handler.send_team_message(
                access_token, target_team["id"], target_channel["id"], message
            )
            
            return {
                "success": True,
                "message": f"Message sent successfully to {channel_name} in {team_name}",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Send message workflow failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_team_report_workflow(
        self, 
        access_token: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive team report"""
        try:
            team_name = parameters.get("team_name")
            report_type = parameters.get("report_type", "general")
            
            # Step 1: Get team info
            teams = await self.plugin_handler.get_user_teams(access_token)
            target_team = None
            for team in teams:
                if team.get("display_name", "").lower() == team_name.lower():
                    target_team = team
                    break
            
            if not target_team:
                return {"success": False, "error": f"Team '{team_name}' not found"}
            
            # Step 2: Get team channels
            channels = await self.plugin_handler.get_team_channels(
                access_token, target_team["id"]
            )
            
            # Step 3: Search for relevant documents
            search_query = f"team {team_name} {report_type} report"
            search_results = await self.plugin_handler.search_documents(
                access_token, search_query, "semantic", 10
            )
            
            # Step 4: Generate report content
            report_content = f"""
# Team Report: {team_name}

## Team Information
- **Team Name**: {target_team.get('display_name')}
- **Description**: {target_team.get('description', 'N/A')}
- **Visibility**: {target_team.get('visibility', 'N/A')}

## Channels ({len(channels)})
{chr(10).join([f"- {channel.get('display_name')} ({'Default' if channel.get('is_default') else 'Standard'})" for channel in channels])}

## Related Documents
Found {search_results.get('total_count', 0)} relevant documents.
            """.strip()
            
            # Step 5: Send report to team
            if parameters.get("send_to_team", True):
                # Find general channel
                general_channel = None
                for channel in channels:
                    if channel.get("display_name", "").lower() in ["general", "announcements"]:
                        general_channel = channel
                        break
                
                if general_channel:
                    await self.plugin_handler.send_team_message(
                        access_token, target_team["id"], general_channel["id"], report_content
                    )
            
            return {
                "success": True,
                "report": report_content,
                "team_info": target_team,
                "channels": channels,
                "search_results": search_results
            }
            
        except Exception as e:
            logger.error(f"Create report workflow failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _search_and_summarize_workflow(
        self, 
        access_token: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search documents and provide summary"""
        try:
            query = parameters.get("query")
            max_results = parameters.get("max_results", 5)
            
            # Step 1: Search documents
            search_results = await self.plugin_handler.search_documents(
                access_token, query, "semantic", max_results
            )
            
            # Step 2: Generate summary using chat
            summary_prompt = f"""
Tóm tắt thông tin từ kết quả tìm kiếm sau:
Query: {query}
Kết quả: {json.dumps(search_results, ensure_ascii=False, indent=2)}

Hãy tóm tắt ngắn gọn và có cấu trúc.
            """.strip()
            
            summary_response = await self.plugin_handler.process_chat_query(
                access_token, summary_prompt
            )
            
            return {
                "success": True,
                "query": query,
                "search_results": search_results,
                "summary": summary_response,
                "total_found": search_results.get("total_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Search and summarize workflow failed: {e}")
            return {"success": False, "error": str(e)}


class AgentHandler:
    """Handler for Microsoft Copilot Agent operations"""
    
    def __init__(self, plugin_handler: CopilotPluginHandler):
        self.plugin_handler = plugin_handler
        self.workflow = AgentWorkflow(plugin_handler)
    
    async def process_agent_request(
        self, 
        access_token: str, 
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process agent request with intent recognition
        
        Args:
            access_token: Azure AD access token
            request: Agent request with intent and parameters
            
        Returns:
            Agent response
        """
        try:
            intent = request.get("intent")
            parameters = request.get("parameters", {})
            context = request.get("context", {})
            
            logger.info(f"Processing agent request: {intent}")
            
            # Handle different intents
            if intent == "send_message":
                return await self._handle_send_message(access_token, parameters, context)
            elif intent == "get_teams":
                return await self._handle_get_teams(access_token, parameters, context)
            elif intent == "search_documents":
                return await self._handle_search_documents(access_token, parameters, context)
            elif intent == "create_report":
                return await self.workflow.execute_workflow(
                    access_token, "create_team_report", parameters
                )
            elif intent == "search_and_summarize":
                return await self.workflow.execute_workflow(
                    access_token, "search_and_summarize", parameters
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown intent: {intent}",
                    "available_intents": [
                        "send_message", "get_teams", "search_documents", 
                        "create_report", "search_and_summarize"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Agent request processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_send_message(
        self, 
        access_token: str, 
        parameters: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle send message intent"""
        try:
            # Use workflow for complex message sending
            return await self.workflow.execute_workflow(
                access_token, "send_team_message", parameters
            )
        except Exception as e:
            logger.error(f"Send message handling failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_get_teams(
        self, 
        access_token: str, 
        parameters: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get teams intent"""
        try:
            teams = await self.plugin_handler.get_user_teams(access_token)
            
            # Format response for agent
            formatted_teams = []
            for team in teams:
                formatted_teams.append({
                    "id": team.get("id"),
                    "name": team.get("display_name"),
                    "description": team.get("description"),
                    "visibility": team.get("visibility")
                })
            
            return {
                "success": True,
                "teams": formatted_teams,
                "count": len(formatted_teams),
                "message": f"Found {len(formatted_teams)} teams"
            }
        except Exception as e:
            logger.error(f"Get teams handling failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_search_documents(
        self, 
        access_token: str, 
        parameters: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle search documents intent"""
        try:
            query = parameters.get("query")
            search_type = parameters.get("search_type", "semantic")
            limit = parameters.get("limit", 10)
            
            results = await self.plugin_handler.search_documents(
                access_token, query, search_type, limit
            )
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_found": results.get("total_count", 0),
                "message": f"Found {results.get('total_count', 0)} documents for '{query}'"
            }
        except Exception as e:
            logger.error(f"Search documents handling failed: {e}")
            return {"success": False, "error": str(e)}


# Global agent handler instance
agent_handler = AgentHandler(CopilotPluginHandler())
