import os
from typing import Literal
from dotenv import load_dotenv
import ldclient
from ldclient import Config, Context
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import MiddlewareContext, Middleware
from tools import conversion, weather

load_dotenv()

mcp = FastMCP("My MCP Server")
LD_SDK_KEY = os.getenv("LD_SDK_KEY", None)
LD_FF_ENABLED_TOOLS = os.getenv("LD_FF_ENABLED_TOOLS", None)
if LD_SDK_KEY is None:
    raise ValueError("LD_SDK_KEY not set")

ldclient.set_config(Config(LD_SDK_KEY))
client = ldclient.get()

if not ldclient.get().is_initialized():
    raise ValueError("LaunchDarkly Initialization Failed")


def get_enabled_tags(tenant_id) -> set[str]:
    context = Context.builder("sgadi-mcp-server").set("tenant_id", tenant_id).build()
    flag_value = client.variation(LD_FF_ENABLED_TOOLS, context, {"enabled": []})
    if isinstance(flag_value, dict) and "enabled" in flag_value:
        return set(flag_value["enabled"])
    return set()


class SetFeatureFlagMiddleware(Middleware):
    async def _apply_feature_flags(self, context: MiddlewareContext):
        headers = get_http_headers()
        if tenant_id := headers.get("x-tenant-id"):
            enabled_tags = get_enabled_tags(tenant_id=tenant_id)
            await context.fastmcp_context.reset_visibility()
            await context.fastmcp_context.enable_components(tags=enabled_tags)

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        await self._apply_feature_flags(context)
        return await call_next(context)

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        await self._apply_feature_flags(context)
        return await call_next(context)


mcp.add_middleware(SetFeatureFlagMiddleware())


@mcp.tool(tags={"public"})
async def greet(name: str) -> str:
    return f"Hello, {name}!"


@mcp.tool(tags={"premium"})
def get_weather(city: str) -> int:
    return weather.get_weather(city)


@mcp.tool(tags={"trail"})
def convert_temperature(temperature: float, unit: Literal["C", "F"]) -> float:
    return conversion.convert_temperature(temperature, unit)


if __name__ == "__main__":
    mcp.enable(tags={"public"}, only=True)
    mcp.run(transport="http", port=8000)
