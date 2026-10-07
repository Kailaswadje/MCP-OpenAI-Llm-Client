from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
llm = OpenAI()

import asyncio
import json


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


from openai import OpenAI




# --------------------------------------------------
# 1. Create OpenAI client
# --------------------------------------------------


llm = OpenAI()




# --------------------------------------------------
# 2. Tell the MCP client how to start our server
# --------------------------------------------------


server_params = StdioServerParameters(
    command="python",
    args=["llmserver.py"],
)




# --------------------------------------------------
# 3. Main function
# --------------------------------------------------


async def main():


    # Connect to MCP server
    async with stdio_client(server_params) as (read, write):


        # Create MCP session
        async with ClientSession(read, write) as session:


            print("Connected to MCP server")


            # --------------------------------------------------
            # 4. Initialize MCP session
            # --------------------------------------------------


            await session.initialize()




            # --------------------------------------------------
            # 5. Discover MCP tools
            # --------------------------------------------------


            tools = await session.list_tools()


            print("\nAvailable MCP Tools:")


            for tool in tools.tools:
                print("-", tool.name)




            # --------------------------------------------------
            # 6. Convert MCP tools into OpenAI tool format
            # --------------------------------------------------


            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in tools.tools
            ]




            # --------------------------------------------------
            # 7. User question
            # --------------------------------------------------


            user_query = "What is 10 + 20?"




            # --------------------------------------------------
            # 8. Send question + tools to LLM
            # --------------------------------------------------


            response = llm.chat.completions.create(


                # LOW-COST MODEL
                model="gpt-4o-mini",


                messages=[
                    {
                        "role": "user",
                        "content": user_query
                    }
                ],


                tools=openai_tools
            )




            # --------------------------------------------------
            # 9. Get LLM response
            # --------------------------------------------------


            message = response.choices[0].message




            # --------------------------------------------------
            # 10. Check whether LLM requested a tool
            # --------------------------------------------------


            if message.tool_calls:


                for tool_call in message.tool_calls:


                    # Get tool name selected by LLM
                    tool_name = tool_call.function.name


                    # Get arguments selected by LLM
                    tool_arguments = json.loads(
                        tool_call.function.arguments
                    )


                    print("\nLLM selected tool:", tool_name)
                    print("Arguments:", tool_arguments)




                    # --------------------------------------------------
                    # 11. Execute the MCP tool
                    # --------------------------------------------------


                    result = await session.call_tool(
                        tool_name,
                        arguments=tool_arguments
                    )




                    print(
                        "MCP Tool Result:",
                        result.structuredContent["result"]
                    )




            else:


                # If no tool is required
                print("\nLLM Answer:")
                print(message.content)




# --------------------------------------------------
# 12. Run the program
# --------------------------------------------------


if __name__ == "__main__":
    asyncio.run(main())
