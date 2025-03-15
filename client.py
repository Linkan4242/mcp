import requests
import json

class MCPClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.context = {}
    
    def list_tools(self):
        payload = {"command": "LIST_TOOLS"}
        response = requests.post(self.server_url + "/mcp", json=payload)
        if response.ok:
            return response.json().get("tools", [])
        else:
            raise Exception("Error listing tools: " + response.text)
    
    def call_tool(self, tool_id, parameters):
        payload = {
            "command": "CALL_TOOL",
            "tool_id": tool_id,
            "parameters": parameters,
            "context": self.context
        }
        response = requests.post(self.server_url + "/mcp", json=payload)
        if response.ok:
            data = response.json()
            self.context.update(data.get("context", {}))
            return data.get("output")
        else:
            raise Exception("Error calling tool: " + response.text)

if __name__ == '__main__':
    client = MCPClient("http://localhost:5000")
    
    # Discover tools
    tools = client.list_tools()
    print("Available Tools:")
    for tool in tools:
        print(f"- {tool['tool_id']}: {tool['name']} - {tool['description']}")
    
    # Execute a series of tasks for an end-to-end workflow
    
    print("\n[1] Code Generation")
    code = client.call_tool("code_generation", {
        "description": "Implement a REST API endpoint for user authentication",
        "language": "Python"
    })
    print("Generated Code:\n", code)
    
    print("\n[2] Debugging")
    debug_result = client.call_tool("debugging", {})
    print("Debug Result:\n", debug_result)
    
    print("\n[3] Testing")
    test_result = client.call_tool("testing", {})
    print("Test Results:\n", test_result)
    
    print("\n[4] Deployment")
    deploy_result = client.call_tool("deployment", {"target": "production"})
    print("Deployment Status:\n", deploy_result)
    
    print("\n[5] Website Check")
    website_status = client.call_tool("website_check", {"url": "https://example.com"})
    print("Website Status:\n", website_status)
    
    print("\n[6] Local Command Execution")
    command_output = client.call_tool("local_command", {"command": "echo 'Hello from local command!'"})
    print("Command Output:\n", command_output)
    
    print("\n[Global Context]")
    print(json.dumps(client.context, indent=2))
