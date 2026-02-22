
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, fn):
        self.tools[name] = fn

    def call(self, name, payload):
        if name not in self.tools:
            raise ValueError(f"Tool {name} not registered")
        return self.tools[name](payload)
