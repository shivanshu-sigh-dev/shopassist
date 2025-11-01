import os
import json
import pandas as pd
import requests

from utils import ai_utils

def fetch_product_details(user_query: str, available_products: pd.DataFrame) -> str:
    messages=[
        {"role": "system", "content": "You are an expert laptop assistant. Use available tools to answer user queries."},
        {"role": "user", "content": user_query},
    ]
    ai_response = ai_utils.perform_chat_completion_with_tools(messages, get_configured_tools())
    return handle_tools_calling(user_query, ai_response, available_products)

def get_configured_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_laptop_data",
                "description": "Search the local CSV file for laptop data related to the user's query. The CSV file holds information about Brand, Model Name, Core, CPU Manufacturer, Clock Speed, RAM Size, Storage Type, Display Type, Display Size, Graphics Processor, Screen Resolution, OS, Laptop Weight, Special Features, Warranty, Average Battery Life, Price, Description.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "laptop_brand": {"type": "string", "description": "The brand of the laptop to search for (e.g., Dell, HP)."},
                        "laptop_model": {"type": "string", "description": "The model of the laptop to search for (e.g., XPS 15)."},
                        "laptop_property": {"type": "string", "description": "Specific property or feature to look for (e.g., battery life, GPU, display resolution)."}
                    },
                    "required": ["laptop_brand", "laptop_model", "laptop_property"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search_langsearch",
                "description": "Search the web for laptop information when not available in the CSV file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "User's question about a laptop."}
                    },
                    "required": ["query"],
                },
            },
        },
    ]

def search_laptop_data(df: pd.DataFrame, laptop_brand: str = "", laptop_model: str = "", laptop_property: str = ""):
    # Preprocess columns for easy lookup
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Search for brand/model in query
    lb = laptop_brand.lower()
    lm = laptop_model.lower()
    lp = laptop_property.lower()
    
    # filter rows where 'model name' is same as lm and 'brand' is same as lb and one of the column names contains the lp
    matches = df[
        (df['brand'].str.lower() == lb) &
        (df['model name'].str.lower() == lm) &
        (df.columns.str.contains(lp).any())
    ]

    if matches.empty:
        return {"found": False, "result": "No matching laptop found in local data."}

    # Convert first match to dict
    laptop_info = matches.iloc[0].to_dict()
    return {"found": True, "result": laptop_info}

def web_search_langsearch(query: str):
    url = "https://api.langsearch.com/v1/web-search"
    payload = {
        "query": query,
        "freshness": "noLimit",
        "summary": True,
        "count": 2
    }
    headers = {
        "authorization": "Bearer " + os.getenv("LANGSEARCH_API_KEY"),
        "content-type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Parse result summaries
        results = []
        for item in data.get("data", []).get("webPages", []).get("value", []):
            results.append({    
                "snippet": item.get("snippet"),
                "summary": item.get("summary")
            })
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": f"Web search failed: {e}"}
    
def handle_tools_calling(user_query:str, ai_response: dict, df: pd.DataFrame) -> str:
    if ai_response.tool_calls:
        for tool_call in ai_response.tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            if tool_name == "search_laptop_data":
                result = search_laptop_data(df, args.get("laptop_brand", ""), args.get("laptop_model", ""), args.get("laptop_property", ""))
                if not result["found"]:
                    web_result = web_search_langsearch(user_query)
                    final_result = web_result
                else:
                    final_result = result
            elif tool_name == "web_search_langsearch":
                final_result = web_search_langsearch(**args)
            else:
                final_result = {"error": "Unknown function call"}

            return ai_utils.perform_chat_completion(messages=[
                {"role": "system", "content": "You are a helpful assistant that answers user queries about laptops in not more than 100 words."},
                {"role": "user", "content": user_query},
                ai_response,
                {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(final_result)},
            ])
    else:
        return ai_response.content