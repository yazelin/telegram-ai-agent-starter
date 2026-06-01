from datetime import datetime
async def run_tool(name:str,args=None):
    if name=="time": return datetime.now().astimezone().isoformat(timespec="seconds")
    if name=="help": return "Try /ask your question or /tool time"
    return f"Unknown tool: {name}"
