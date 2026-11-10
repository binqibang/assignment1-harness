CALL_TOOL_PROMPT = '''
To call a tool, specify its name and provide the arguments as a JSON object can be parsed directly by Python's `json.loads()` with xml tags <tool_call> </tool_call>. Example:",
<tool_call>{"name": "add", "arguments": {"a": 1, "b": 2}}</tool_call>
'''