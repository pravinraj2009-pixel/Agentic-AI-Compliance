
from src.mcp.tool_registry import ToolRegistry

class MCPServer:
    def __init__(self):
        self.registry = ToolRegistry()

    def register_tool(self, name, fn):
        self.registry.register(name, fn)

    def call_tool(self, name, payload):
        return self.registry.call(name, payload)
