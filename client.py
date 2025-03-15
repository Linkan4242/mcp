import os
import json
import requests
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global context to maintain state between calls
GLOBAL_CONTEXT = {}

# ----------------------------------
# Tool Implementations
# ----------------------------------

def code_generation_tool(params, context):
    """
    Simulate code generation based on a description.
    In a production system, you might integrate with an LLM.
    """
    description = params.get("description", "No description provided")
    language = params.get("language", "Python")
    # Stub code generation (replace with your AI integration)
    code = f"# {language} code generated for: {description}\ndef generated_function():\n    pass"
    context["generated_code"] = code
    return code, context

def debugging_tool(params, context):
    """
    Simulate debugging by checking if generated code exists.
    """
    code = context.get("generated_code", "")
    if code:
        debug_result = "No issues found." if "def" in code else "Error: No function definition detected."
    else:
        debug_result = "No code available to debug."
    context["debug_result"] = debug_result
    return debug_result, context

def testing_tool(params, context):
    """
    Simulate running tests.
    """
    test_result = "All tests passed."  # Replace with real testing logic
    context["test_result"] = test_result
    return test_result, context

def deployment_tool(params, context):
    """
    Simulate deployment.
    """
    target = params.get("target", "staging")
    deployment_result = f"Deployed successfully to {target}."
    context["deployment_result"] = deployment_result
    return deployment_result, context

def website_check_tool(params, context):
    """
    Check the status of a website via HTTP GET.
    """
    url = params.get("url", "https://example.com")
    try:
        response = requests.get(url, timeout=5)
        status = f"Website {url} returned status {response.status_code}"
    except Exception as e:
        status = f"Error checking website: {str(e)}"
    context["website_status"] = status
    return status, context

def local_command_tool(params, context):
    """
    Execute a local shell command.
    """
    command = params.get("command")
    if not command:
        return "No command provided.", context
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
        result = output.decode("utf-8")
    except Exception as e:
        result = f"Error executing command: {str(e)}"
    context["command_output"] = result
    return result, context

def get_latest_commit(owner, repo):
    """
    Fetch the latest commit from a GitHub repository using the REST API.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise Exception("GITHUB_TOKEN is not set in your environment.")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"GitHub API error {response.status_code}: {response.text}"}
    
    commits = response.json()
    if not commits:
        return {"error": "No commits found."}
    
    latest = commits[0]
    return {
        "sha": latest.get("sha", ""),
        "message": latest.get("commit", {}).get("message", ""),
        "author": latest.get("commit", {}).get("author", {}).get("name", "")
    }

def latest_commit_tool(params, context):
    """
    Use the GitHub API to fetch the latest commit.
    """
    owner = params.get("owner", "Linkan4242")
    repo = params.get("repo", "mcp")
    result = get_latest_commit(owner, repo)
    context["latest_commit"] = result
    return result, context

# ----------------------------------
# Tool Registry and Dispatcher
# ----------------------------------

def list_tools():
    """
    Return the list of available MCP tools.
    """
    tools = [
        {
            "tool_id": "code_generation",
            "name": "Code Generation",
            "description": "Generate code based on a description.",
            "parameters": {"description": "string", "language": "string"}
        },
        {
            "tool_id": "debugging",
            "name": "Debugging",
            "description": "Analyze generated code for issues.",
            "parameters": {}
        },
        {
            "tool_id": "testing",
            "name": "Testing",
            "description": "Run tests on the current code.",
            "parameters": {}
        },
        {
            "tool_id": "deployment",
            "name": "Deployment",
            "description": "Deploy the current build to a target environment.",
            "parameters": {"target": "string"}
        },
        {
            "tool_id": "website_check",
            "name": "Website Check",
            "description": "Check the status of a website.",
            "parameters": {"url": "string"}
        },
        {
            "tool_id": "local_command",
            "name": "Local Command Execution",
            "description": "Execute a local shell command.",
            "parameters": {"command": "string"}
        },
        {
            "tool_id": "latest_commit",
            "name": "Fetch Latest Commit",
            "description": "Fetch the latest commit from a GitHub repository using the REST API.",
            "parameters": {"owner": "string", "repo": "string"}
        }
    ]
    return tools

def handle_call_tool(tool_id, parameters, context):
    """
    Dispatch the tool call based on tool_id.
    """
    if tool_id == "code_generation":
        return code_generation_tool(parameters, context)
    elif tool_id == "debugging":
        return debugging_tool(parameters, context)
    elif tool_id == "testing":
        return testing_tool(parameters, context)
    elif tool_id == "deployment":
        return deployment_tool(parameters, context)
    elif tool_id == "website_check":
        return website_check_tool(parameters, context)
    elif tool_id == "local_command":
        return local_command_tool(parameters, context)
    elif tool_id == "latest_commit":
        return latest_commit_tool(parameters, context)
    else:
        return {"error": "Tool not found."}, context

# ----------------------------------
# MCP Server Endpoint
# ----------------------------------

@app.route("/mcp", methods=["POST"])
def mcp_handler():
    """
    MCP endpoint to handle commands.
    Supports "LIST_TOOLS" and "CALL_TOOL" commands.
    """
    data = request.get_json()
    command = data.get("command")
    
    if command == "LIST_TOOLS":
        return jsonify({"status": "success", "tools": list_tools()})
    elif command == "CALL_TOOL":
        tool_id = data.get("tool_id")
        parameters = data.get("parameters", {})
        context = GLOBAL_CONTEXT.copy()
        context.update(data.get("context", {}))
        
        result, updated_context = handle_call_tool(tool_id, parameters, context)
        GLOBAL_CONTEXT.update(updated_context)
        return jsonify({"status": "success", "output": result, "context": GLOBAL_CONTEXT})
    else:
        return jsonify({"status": "error", "message": "Invalid command."}), 400

if __name__ == "__main__":
    # Run the server on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
