import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('../.env')
ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def perform_chat_completion(messages: list) -> str:
    completion = ai_client.chat.completions.create(
        model="o4-mini",
        messages=messages
    )
    return completion.choices[0].message.content

def perform_moderation_check(input_text: str) -> bool:
    response = ai_client.moderations.create(
        model="omni-moderation-latest",
        input=input_text
    )
    return response.results[0].flagged

def perform_chat_completion_with_tools(messages: list, tools: list) -> dict:
    response = ai_client.chat.completions.create(
        model="o4-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    return response.choices[0].message