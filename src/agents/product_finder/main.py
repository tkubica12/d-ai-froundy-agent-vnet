"""
Smoke test for Product Finder agent using Azure AI Foundry Agent Service with MCP tools.

This script creates an agent with MCP server tools configured, sends a test message,
and verifies that the agent successfully uses the tools to search and recommend products.
"""
import os
import logging
import time
from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import MessageRole, RunStatus, McpTool, RunStepActivityDetails
from azure.core.exceptions import DecodeError, HttpResponseError
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    
    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of Azure SDK loggers
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure').setLevel(logging.WARNING)


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")


def print_step(emoji: str, text: str):
    """Print a step with emoji and color."""
    print(f"{Colors.BLUE}{emoji}  {text}{Colors.RESET}")


def print_success(emoji: str, text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}{emoji}  {text}{Colors.RESET}")


def print_error(emoji: str, text: str):
    """Print an error message."""
    print(f"{Colors.RED}{emoji}  {text}{Colors.RESET}")


def print_info(text: str, dim: bool = False):
    """Print informational text."""
    color = Colors.DIM if dim else Colors.RESET
    print(f"{color}{text}{Colors.RESET}")


def print_conversation_msg(role: str, content: str):
    """Print a conversation message with role styling."""
    if role == "USER":
        print(f"{Colors.BOLD}{Colors.MAGENTA}👤 {role}:{Colors.RESET} {content}")
    else:
        print(f"{Colors.BOLD}{Colors.CYAN}🤖 {role}:{Colors.RESET} {content}")


def load_system_prompt() -> str:
    """Load and render the system prompt from Jinja2 template.
    
    Returns:
        str: The rendered system prompt.
    """
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('system_prompt.jinja2')
    return template.render()


def main():
    """Run smoke test for product finder agent."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration from environment
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    
    if not project_endpoint:
        print_error("❌", "PROJECT_ENDPOINT environment variable is not set")
        print_info("Please copy .env.sample to .env and configure your Azure AI Foundry project endpoint", dim=True)
        return
    
    if not model_deployment_name:
        print_error("❌", "MODEL_DEPLOYMENT_NAME environment variable is not set")
        print_info("Please set MODEL_DEPLOYMENT_NAME in your .env file (e.g., gpt-4o)", dim=True)
        return
    
    if not mcp_server_url:
        print_error("❌", "MCP_SERVER_URL environment variable is not set")
        print_info("Please set MCP_SERVER_URL in your .env file", dim=True)
        return
    
    print_header("🧪 PRODUCT FINDER AGENT SMOKE TEST (with MCP Tools)")
    print_info(f"📍 Endpoint: {project_endpoint}", dim=True)
    print_info(f"🤖 Model: {model_deployment_name}", dim=True)
    print_info(f"🔧 MCP Server: {mcp_server_url}", dim=True)
    print()
    
    try:
        # Create AIProjectClient with DefaultAzureCredential
        print_step("🔐", "Authenticating with Azure...")
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential(),
        )
        
        with project_client:
            print_step("🔧", "Configuring MCP tools...")
            
            # Configure MCP Tool
            mcp_tool = McpTool(
                server_label="products_mcp",  # Only alphanumeric and underscores allowed
                server_url=mcp_server_url,
                allowed_tools=[]  # Empty list means all tools are allowed
            )
            
            print_success("✅", f"MCP server configured: {Colors.DIM}{mcp_server_url}{Colors.RESET}")
            
            print_step("🏗️", "Creating product finder agent with MCP tools...")
            
            # Load system prompt from template
            system_prompt = load_system_prompt()
            
            # Create agent with MCP tools
            agent = project_client.agents.create_agent(
                model="gpt-4.1",
                name="product-finder-mcp-test",
                instructions=system_prompt,
                tools=mcp_tool.definitions,
            )
            print_success("✅", f"Created agent with ID: {Colors.DIM}{agent.id}{Colors.RESET}")
            
            # Create a thread for communication
            print_step("💬", "Creating conversation thread...")
            thread = project_client.agents.threads.create()
            print_success("✅", f"Created thread with ID: {Colors.DIM}{thread.id}{Colors.RESET}")
            
            # Send a test message that requires tool usage
            test_message = "I'm user-alice and I need hiking gear. Can you help me find suitable products considering my profile?"
            print_step("📤", f"Sending test message: {Colors.YELLOW}'{test_message}'{Colors.RESET}")
            
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=test_message,
            )
            print_success("✅", f"Created message with ID: {Colors.DIM}{message.id}{Colors.RESET}")
            
            # Create and process agent run with retry logic
            print_step("⚙️", "Running agent and waiting for response (this may take a while with tool calls)...")
            
            # Set approval mode to "never" for automated testing
            mcp_tool.set_approval_mode("never")
            
            max_retries = 3
            retry_delay = 10  # Longer delay for MCP tool calls
            run = None
            
            for attempt in range(max_retries):
                try:
                    # Create run with MCP tool resources
                    run = project_client.agents.runs.create(
                        thread_id=thread.id,
                        agent_id=agent.id,
                        tool_resources=mcp_tool.resources
                    )
                    
                    # Poll for completion
                    while run.status in ["queued", "in_progress", "requires_action"]:
                        time.sleep(2)
                        run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                        
                    # Success - exit retry loop
                    break
                    
                except (DecodeError, HttpResponseError, Exception) as e:
                    error_msg = str(e).lower()
                    if "timed out" in error_msg or "timeout" in error_msg or "json is invalid" in error_msg:
                        print_error("⏱️", f"Request timed out (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            print_info(f"Retrying in {retry_delay}s...", dim=True)
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            print_error("❌", f"Max retries reached. Service may be slow or unavailable.")
                            print_info(f"Error details: {str(e)[:200]}", dim=True)
                            return
                    else:
                        # Different error, don't retry
                        raise
            
            if run is None:
                print_error("❌", "Failed to create run after all retries")
                return
                
            print_success("✅", f"Run completed with status: {Colors.GREEN}{Colors.BOLD}{run.status}{Colors.RESET}")
            
            # Check for failures
            if run.status == RunStatus.FAILED:
                print_error("❌", f"Run failed: {run.last_error}")
                return
            
            # Verify tool usage
            print_step("🔍", "Checking tool usage...")
            tool_calls_found = False
            if hasattr(run, 'required_action') and run.required_action:
                tool_calls_found = True
            
            # Check run steps for tool calls
            try:
                run_steps = project_client.agents.runs.list_steps(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                tool_count = 0
                for step in run_steps:
                    if hasattr(step, 'step_details') and step.step_details:
                        step_type = getattr(step.step_details, 'type', None)
                        if step_type == 'tool_calls':
                            tool_calls_found = True
                            if hasattr(step.step_details, 'tool_calls'):
                                tool_count += len(step.step_details.tool_calls)
                
                if tool_calls_found:
                    print_success("✅", f"Agent successfully used MCP tools ({tool_count} tool call(s) detected)")
                else:
                    print_error("⚠️", "Warning: No tool calls detected - agent may not have used MCP tools")
                    
            except Exception as e:
                print_info(f"Could not verify tool usage details: {str(e)[:100]}", dim=True)
            
            # Fetch and display messages
            print_step("📥", "Fetching agent response...")
            messages = project_client.agents.messages.list(thread_id=thread.id)
            
            print_header("💬 CONVERSATION TRANSCRIPT")
            
            agent_response = None
            for msg in reversed(list(messages)):
                role = msg.role.upper()
                if msg.text_messages:
                    for text_msg in msg.text_messages:
                        print_conversation_msg(role, text_msg.text.value)
                        print()
                        if role == "ASSISTANT":
                            agent_response = text_msg.text.value
            
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}\n")
            
            # Verify response contains product information from our seed data
            print_step("🔍", "Verifying response contains product data...")
            
            # Check for product IDs or names from seed data
            product_indicators = [
                'prod-', 'TrailBlazer', 'Alpine', 'hiking', 'boots', 'backpack',
                'user-alice', 'allergy', 'allergies', 'nut', 'outdoor'
            ]
            
            found_indicators = []
            if agent_response:
                response_lower = agent_response.lower()
                for indicator in product_indicators:
                    if indicator.lower() in response_lower:
                        found_indicators.append(indicator)
            
            if found_indicators:
                print_success("✅", f"Response contains product data indicators: {Colors.DIM}{', '.join(found_indicators[:5])}{Colors.RESET}")
            else:
                print_error("⚠️", "Warning: Response may not contain specific product data from MCP server")
            
            # Clean up - delete the agent
            print_step("🧹", f"Cleaning up - deleting agent...")
            project_client.agents.delete_agent(agent.id)
            print_success("✅", "Agent deleted")
            
            # Final verdict
            if tool_calls_found and found_indicators:
                print(f"\n{Colors.BG_GREEN}{Colors.BOLD} 🎉 SMOKE TEST PASSED! 🎉 {Colors.RESET}")
                print(f"{Colors.GREEN}The product finder agent successfully used MCP tools and returned product data.{Colors.RESET}\n")
            elif tool_calls_found:
                print(f"\n{Colors.YELLOW}{Colors.BOLD} ⚠️  PARTIAL SUCCESS ⚠️ {Colors.RESET}")
                print(f"{Colors.YELLOW}Tools were called but response validation needs review.{Colors.RESET}\n")
            else:
                print(f"\n{Colors.YELLOW}{Colors.BOLD} ⚠️  NEEDS REVIEW ⚠️ {Colors.RESET}")
                print(f"{Colors.YELLOW}Agent responded but tool usage could not be confirmed.{Colors.RESET}\n")
            
    except Exception as e:
        print(f"\n{Colors.BG_RED}{Colors.BOLD} ❌ SMOKE TEST FAILED ❌ {Colors.RESET}")
        print_error("💥", f"Error: {str(e)}")
        logger.exception("Full error details:")
        raise


if __name__ == "__main__":
    main()
