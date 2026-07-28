"""
Connector Generator — Generates the bridge code between a BPM engine
and a Strands AI agent for individual task replacement.

Produces:
  1. A Strands agent for the replaced task
  2. A REST API wrapper (FastAPI) so the BPM engine can call it
  3. BPM connector config (for Camunda/Flowable/Kogito)
  4. Input/output schema mapping
"""
import json
import os
from dataclasses import dataclass, field
from augmentor.task_evaluator import TaskEvaluation, ReplacementVerdict


@dataclass
class ConnectorOutput:
    """Generated files for a single task replacement."""
    task_id: str
    task_name: str
    files: dict = field(default_factory=dict)  # filename -> content


def generate_connectors(
    evaluations: list[TaskEvaluation],
    output_dir: str,
    bpm_engine: str = "camunda",
) -> list[ConnectorOutput]:
    """
    Generate agent + connector code for tasks marked as candidates.
    Only generates for STRONG_CANDIDATE and GOOD_CANDIDATE tasks.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "agents"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "connectors"), exist_ok=True)

    outputs = []
    candidates = [
        e for e in evaluations
        if e.verdict in (ReplacementVerdict.STRONG_CANDIDATE,
                         ReplacementVerdict.GOOD_CANDIDATE)
    ]

    for eval_item in candidates:
        output = _generate_single_connector(eval_item, output_dir, bpm_engine)
        outputs.append(output)

    # Generate shared API server
    _generate_api_server(candidates, output_dir)

    # Generate deployment config
    _generate_deployment_config(candidates, output_dir)

    print(f"Generated connectors for {len(outputs)} tasks in: {output_dir}")
    return outputs



def _generate_single_connector(
    eval_item: TaskEvaluation,
    output_dir: str,
    bpm_engine: str,
) -> ConnectorOutput:
    """Generate agent + connector for a single task."""
    safe_name = eval_item.element_id.replace("-", "_").replace(" ", "_")
    files = {}

    # 1. Strands Agent
    agent_code = _build_agent_code(eval_item, safe_name)
    agent_path = os.path.join(output_dir, "agents", f"{safe_name}_agent.py")
    with open(agent_path, "w") as f:
        f.write(agent_code)
    files[f"agents/{safe_name}_agent.py"] = agent_path

    # 2. Connector config for the BPM engine
    connector_config = _build_connector_config(eval_item, safe_name, bpm_engine)
    config_path = os.path.join(output_dir, "connectors", f"{safe_name}_connector.json")
    with open(config_path, "w") as f:
        json.dump(connector_config, f, indent=2)
    files[f"connectors/{safe_name}_connector.json"] = config_path

    return ConnectorOutput(
        task_id=eval_item.element_id,
        task_name=eval_item.element_name,
        files=files,
    )


def _build_agent_code(eval_item: TaskEvaluation, safe_name: str) -> str:
    """Generate a Strands agent that replaces a BPMN task."""
    has_human_fallback = eval_item.score.risk >= 0.5

    fallback_tool = ""
    fallback_import = ""
    fallback_in_tools = ""
    if has_human_fallback:
        fallback_tool = '''

@tool
def escalate_to_human(reason: str, context: str) -> str:
    """Escalate to human when confidence is below threshold."""
    # TODO: Push to human task queue or notification system
    return json.dumps({
        "escalated": True,
        "reason": reason,
        "context": context,
    })
'''
        fallback_in_tools = ", escalate_to_human"

    confidence_instruction = ""
    if has_human_fallback:
        confidence_instruction = """
If your confidence in the decision is below 80%, use the escalate_to_human tool
instead of returning a direct result. Include your partial analysis as context."""

    return f'''"""
Agent: {eval_item.element_name}
Replaces BPMN task: {eval_item.element_id} ({eval_item.element_type})
{eval_item.agent_description}

Integration: {eval_item.integration_approach}
"""
import json
from strands import Agent, tool
from strands.models.bedrock import BedrockModel


@tool
def process_task(input_data: str) -> str:
    """Process the task with the given input data from the BPM engine.

    Args:
        input_data: JSON string with process variables from the BPM engine.

    Returns:
        JSON string with task results in the format the BPM engine expects.
    """
    data = json.loads(input_data)
    # TODO: Implement task-specific logic
    # The agent's LLM reasoning handles the core logic via system prompt.
    # This tool is for structured I/O with external systems if needed.
    return json.dumps({{"status": "completed", "input_received": data}})
{fallback_tool}

SYSTEM_PROMPT = """You are an AI agent that replaces the BPM task: {eval_item.element_name}.

{eval_item.agent_description}

You receive process variables as JSON from the BPM engine. Analyze the input,
perform the task, and return a structured JSON response that the BPM engine
can use to continue the workflow.
{confidence_instruction}
Always return valid JSON with at minimum a "status" field ("completed" or "error")
and a "result" field with your output."""

model = BedrockModel(model_id="anthropic.claude-sonnet-4-20250514")

{safe_name}_agent = Agent(
    name="{safe_name}",
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[process_task{fallback_in_tools}],
)


def invoke(process_variables: dict) -> dict:
    """Entry point called by the REST API connector."""
    prompt = f"Process this BPM task with these variables: {{json.dumps(process_variables)}}"
    result = {safe_name}_agent(prompt)
    # Parse agent response as JSON
    response_text = str(result)
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {{"status": "completed", "result": response_text}}
'''


def _build_connector_config(
    eval_item: TaskEvaluation,
    safe_name: str,
    bpm_engine: str,
) -> dict:
    """Build BPM engine connector configuration."""
    base_config = {
        "task_id": eval_item.element_id,
        "task_name": eval_item.element_name,
        "task_type": eval_item.element_type,
        "agent_endpoint": f"/api/agents/{safe_name}/invoke",
        "method": "POST",
        "timeout_seconds": 30,
        "retry_policy": {
            "max_retries": 2,
            "backoff_seconds": 5,
        },
        "input_mapping": {
            "description": "Map BPM process variables to agent input",
            "variables": "all",  # pass all process variables
        },
        "output_mapping": {
            "description": "Map agent response back to BPM process variables",
            "result_variable": f"{safe_name}_result",
        },
    }

    if eval_item.score.risk >= 0.5:
        base_config["human_fallback"] = {
            "enabled": True,
            "confidence_threshold": 0.8,
            "fallback_task_queue": "human-review",
        }

    # Engine-specific config
    if bpm_engine == "camunda":
        base_config["camunda"] = {
            "connector_type": "http-json",
            "topic": f"agent-{safe_name}",
            "worker_id": f"agent-worker-{safe_name}",
        }
    elif bpm_engine == "flowable":
        base_config["flowable"] = {
            "delegate_expression": f"${{agentConnector_{safe_name}}}",
            "async": True,
        }
    elif bpm_engine == "kogito":
        base_config["kogito"] = {
            "work_item_handler": f"AgentHandler_{safe_name}",
            "service_task_type": "rest",
        }

    return base_config


def _generate_api_server(
    candidates: list[TaskEvaluation],
    output_dir: str,
) -> None:
    """Generate a FastAPI server that exposes all agent endpoints."""
    imports = []
    routes = []

    for eval_item in candidates:
        safe_name = eval_item.element_id.replace("-", "_").replace(" ", "_")
        imports.append(
            f"from agents.{safe_name}_agent import invoke as invoke_{safe_name}"
        )
        routes.append(f'''
@app.post("/api/agents/{safe_name}/invoke")
async def {safe_name}_endpoint(request: AgentRequest):
    """Replaces BPMN task: {eval_item.element_name}"""
    result = invoke_{safe_name}(request.process_variables)
    return AgentResponse(
        task_id="{eval_item.element_id}",
        status=result.get("status", "completed"),
        result=result,
    )
''')

    code = f'''"""
Agent API Server — REST endpoints for BPM engine integration.

The BPM engine calls these endpoints instead of the original task
implementations. Each endpoint wraps a Strands AI agent.
"""
from fastapi import FastAPI
from pydantic import BaseModel

{chr(10).join(imports)}


class AgentRequest(BaseModel):
    process_variables: dict
    process_instance_id: str = ""
    task_id: str = ""


class AgentResponse(BaseModel):
    task_id: str
    status: str
    result: dict


app = FastAPI(
    title="BPM Agent Connectors",
    description="AI agent endpoints that replace BPMN tasks",
)


@app.get("/health")
async def health():
    return {{"status": "healthy", "agents": {len(candidates)}}}

{"".join(routes)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''
    with open(os.path.join(output_dir, "api_server.py"), "w") as f:
        f.write(code)


def _generate_deployment_config(
    candidates: list[TaskEvaluation],
    output_dir: str,
) -> None:
    """Generate deployment configuration."""
    agents_config = []
    for eval_item in candidates:
        safe_name = eval_item.element_id.replace("-", "_").replace(" ", "_")
        agents_config.append({
            "name": safe_name,
            "task_id": eval_item.element_id,
            "task_name": eval_item.element_name,
            "endpoint": f"/api/agents/{safe_name}/invoke",
            "verdict": eval_item.verdict.value,
            "risk_level": "high" if eval_item.score.risk >= 0.5 else "low",
            "has_human_fallback": eval_item.score.risk >= 0.5,
        })

    config = {
        "deployment": {
            "mode": "augmentation",
            "description": "BPM engine stays as orchestrator, individual tasks replaced by AI agents",
            "api_server": {
                "host": "0.0.0.0",
                "port": 8080,
                "health_endpoint": "/health",
            },
            "agents": agents_config,
        }
    }

    with open(os.path.join(output_dir, "deployment_config.json"), "w") as f:
        json.dump(config, f, indent=2)
