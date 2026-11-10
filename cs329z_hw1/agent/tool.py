import json
import re
import jsonschema
from cs329z_hw1.types import ParsedResponse, ToolCall, ToolResult, ToolSpec, Status


class ToolRegister:

    def __init__(self, tools: list[ToolSpec]):
        self.tools = tools
        self.tool_dict = {tool.name: tool for tool in tools}

    def schemas(self) -> list[dict]:
        return  [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]

    def _check(self, name: str, args: dict) -> ToolResult | None:
        if name not in self.tool_dict:
            return ToolResult("unknown_tool", f"{name} is not existed.")
        
        tool = self.tool_dict[name]
        try:
            jsonschema.validate(instance=args, schema=tool.parameters)
        except jsonschema.ValidationError as e:
            return ToolResult(status="invalid_args", content=e.message)
        except jsonschema.SchemaError as e:
            # A broken schema is treated as "args can never be valid".
            return ToolResult(status="invalid_args", content=str(e))
        return None

    def validate(self, name: str, args: dict) -> ToolResult | None:
        return self._check(name, args)
        
    def execute(self, name: str, args: dict) -> ToolResult:
        check_res = self._check(name, args)
        if check_res is not None:
            return check_res

        tool = self.tool_dict[name]
        try:
            value = tool.fn(**args)
        except Exception as e:
            return ToolResult(status="tool_error", content=str(e))

        return ToolResult(status="ok", content=str(value))


def parse(text: str) -> ParsedResponse:
    # 1. 只找第一个 <tool_call:N>（避免被参数值中的假标签干扰）
    match = re.search(r'<tool_call:(\d+)>', text)
    if not match:
        return ParsedResponse(text=text.strip(), tool_call=None, error=None)

    start = match.start()
    length = int(match.group(1))
    json_start = match.end()
    json_end = json_start + length          # ✅ 字符位置，与 len() 一致

    # 2. 截断检测
    if json_end > len(text):
        return ParsedResponse(text=text.strip(), tool_call=None,
                              error="truncated tool call")

    # 3. 验证结束标签
    end_tag = "</tool_call>"
    if text[json_end:json_end + len(end_tag)] != end_tag:
        return ParsedResponse(text=text.strip(), tool_call=None,
                              error="missing or malformed closing tag")

    end = json_end + len(end_tag)

    # 4. 检查结束标签之后是否还有额外的调用（真正的"多调用"）
    if re.search(r'<tool_call:\d+>', text[end:]):
        return ParsedResponse(text=text.strip(), tool_call=None,
                              error="multiple tool calls found")

    call_json = text[json_start:json_end]
    new_text = (text[:start] + text[end:]).strip()

    # 5. 解析 JSON（json.loads 原生支持 Unicode）
    try:
        call_dict = json.loads(call_json)
    except (json.JSONDecodeError, ValueError) as e:
        return ParsedResponse(text=new_text, tool_call=None,
                              error=f"invalid tool call JSON: {e}")

    if not isinstance(call_dict, dict):
        return ParsedResponse(text=new_text, tool_call=None,
                              error="tool call must be a JSON object")

    if "name" not in call_dict or "arguments" not in call_dict:
        return ParsedResponse(text=new_text, tool_call=None,
                              error="tool call missing 'name' or 'arguments'")

    tool_call = ToolCall(name=call_dict["name"], args=call_dict["arguments"])
    return ParsedResponse(text=new_text, tool_call=tool_call, error=None)