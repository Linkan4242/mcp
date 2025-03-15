from flask import Flask, request, jsonify
import subprocess
import requests

app = Flask(__name__)
GLOBAL_CONTEXT = {}

# --- Tool Functions ---

def generate_code(params, context):
    description = params.get("description", "No description provided")
    language = params.get("language", "Python")
    code = f"# {language} code generated for: {description}\ndef example():\n    pass"
    context["last_generated_code"] = code
    return code, context

def debug_code(params, context):
    code_snippet = context.get("last_generated_code", "")
    debug_info = "No issues found." if "def" in code_snippet else "Warning: No function definition found."
    context["debug_info"] = debug_info
    return debug_info, context

def run_tests(params, context):
    test_results = "All tests passed."  # Simulated test result
    context["last_test_results"] = test_results
    return test_results, context

def deploy_build(params, context):
    target = params.get("target", "staging")
    deployment_status = f"Deployed to {target} successfully."
    context["deployment_status"] = deployment_status
    return deployment_status, context

def monitor_system(params, context):
    monitoring_report = "System operational. No alerts."
    context["monitoring_report"] = monitoring_report
    return monitoring_report, context

def check_website(params, context):
    url = params.get("url", "http://example.com")
    try:
        response = requests.get(url, timeout=5)
        status = f"Website {url} returned status {response.status_code}"
    except Exception as e:
        status = f"Error checking website: {str(e)}"
    context["website_status"] = status
    return status, context

def execute_command(params, context):
    command = params.get("command")
    if not command:
        return "No command provided.", context
    try:
        # Run the command locally (caution: use with trusted input)
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
        result = output.decode('utf-8')
    except Exception as e:
        result = f"Error executing command: {str(e)}"
    context["last_command_output"] = result
    return result, context

# --- Tool Registry ---
TOOLS = {
    "code_generation": {
        "name": "Code Generation",
        "description": "Generate code based on a high-level description.",
        "parameters": {"description": "string", "language": "string"},
        "function": generate_code
    },
    "debugging": {
        "name": "Debugging",
        "description": "Analyze the last generated code for issues.",
        "parameters": {},
        "function": debug_code
    },
    "testing": {
        "name": "Testing",
        "description": "Run tests on the current code base.",
        "parameters": {},
        "function": run_tests
    },
    "deployment": {
        "name": "Deployment",
        "description": "Deploy the current build to a specified environment.",
        "parameters": {"target": "string"},
        "function": deploy_build
    },
    "monitoring": {
        "name": "Monitoring",
        "description": "Monitor system performance and health.",
        "parameters": {},
        "function": monitor_system
    },
    "website_check": {
        "name": "Website Check",
        "description": "Check the status of a website.",
        "parameters": {"url": "string"},
        "function": check_website
    },
    "local_command": {
        "name": "Local Command Execution",
        "description": "Execute a local shell command.",
        "parameters": {"command": "string"},
        "function": execute_command
    }
}

# --- API Endpoint ---
@app.route('/mcp', methods=['POST'])
def mcp_handler():
    data = request.get_json()
    command = data.get("command")
    
    if command == "LIST_TOOLS":
        tools_list = []
        for tool_id, tool in TOOLS.items():
            tools_list.append({
                "tool_id": tool_id,
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            })
        return jsonify({"status": "success", "tools": tools_list})
    
    elif command == "CALL_TOOL":
        tool_id = data.get("tool_id")
        parameters = data.get("parameters", {})
        context = GLOBAL_CONTEXT.copy()
        context.update(data.get("context", {}))
        
        if tool_id in TOOLS:
            try:
                tool_func = TOOLS[tool_id]["function"]
                output, updated_context = tool_func(parameters, context)
                GLOBAL_CONTEXT.update(updated_context)
                return jsonify({"status": "success", "output": output, "context": GLOBAL_CONTEXT})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            return jsonify({"status": "error", "message": f"Tool {tool_id} not found."}), 404
    else:
        return jsonify({"status": "error", "message": "Invalid command."}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
