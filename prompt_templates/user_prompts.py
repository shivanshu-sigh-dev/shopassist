def get_product_detail_extractor_agent_user_prompt(user_message: str) -> str:
    return f"""
    Here is the user’s request:  
    ```
    {user_message}
    ```  

    From this request, extract the **brand**, **model**, and **property**.  
    - If all three are clear, output them in JSON.  
    - If not, ask a clarifying question to capture the missing detail(s).
    """