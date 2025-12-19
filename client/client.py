import os
import readline
#landchain imports
from langchain.agents import create_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI, HarmCategory, HarmBlockThreshold
#mcp imports
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
             safety_settings = {
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
             }
      )

prompt = ( 
  "You are a STRICT and DETERMINISTIC Book Recommendation Agent.\n\n"

    "RULES YOU MUST FOLLOW:\n"
    "1. ALWAYS return structured JSON, never plain text.\n"
    "2. When calling 'locate_book', store the returned JSON in 'last_located_book'.\n"
    "3. NEVER change, rewrite, guess, or infer title, author, or genre.\n"
    "4. Ask the user for confirmation using JSON in the following format:\n"
    "   {\"action\":\"confirm_book\",\"title\":last_located_book.title,"
    "\"author\":last_located_book.author,\"genre\":last_located_book.genre}\n"
    "5. Only call 'recommend_books' after the user responds with yes to the confirmation.\n"
    "6. If a tool returns an error, stop immediately and display the error.\n\n"

    "FLOW:\n"
    "Step A: User provides a book + author → call locate_book.\n"
    "Step B: Return JSON asking for confirmation of the located book in plain english.\n"
    "Step C: If user confirms, call recommend_books using cached JSON.\n"
    "Step D: Display recommendations in JSON format:\n"
    "   {\"recommendations\": [\"Book Title by Author\", ...]}\n"
    "Step E: Never infer, guess, or change values.\n"
    "Step F: Ask the user if they would like to see bookstores, if so you use find_bookstores\n"
)
#cool header
def print_header():
    """
    Prints a wide ASCII book header for the application start.
    """
    title, subtitle  = "Gemini Book Agent", "v0.1 MCP Client"
    width = 46  # Fixed width for the header look
    
    print(r"      .__________________________________________________.")
    print(r"     /                                                  /|")
    print(f"    |  {title.center(width)}  | |")
    print(f"    |  {subtitle.center(width)}  | |")
    print(r"    |  ______________________________________________  | |")
    print(r"    |                                                  | |")
    print(r"    |__________________________________________________| /")
    print(r"    |__________________________________________________|/")
    print("\n")

async def run_agent():
    async with streamablehttp_client(f"{os.getenv('MCP_URL')}/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await load_mcp_tools(session)
            agent = create_agent(model=llm, tools=tools, system_prompt=prompt)

            print(f"Google Book Recommendation Agent. Enter 'quit' to exit."\
            "Please enter a book title and author.")
            print_header()

            while True:
                user_input = input("Awaiting Input: ")
                if user_input and user_input.lower() != 'quit':
                    try:
                        result = await agent.ainvoke({"messages": [("user", user_input)]})

                        if "messages" in result:
                            messages = result["messages"]
                            if messages:
                                last_message = messages[-1]
                                if hasattr(last_message, 'content'):
                                    print(f"{last_message.content}")
                                else:
                                    print(f"{last_message}")
                            else:
                                print("No response from agent")
                        else:
                            print(f"Agent response: {result}")
                    except Exception as e:
                        print(f"Error: {e}")
        
                else:
                    print("Exiting the agent. Goodbye!")
                    break

if __name__ == "__main__":
    result = asyncio.run(run_agent())
    print(result)
