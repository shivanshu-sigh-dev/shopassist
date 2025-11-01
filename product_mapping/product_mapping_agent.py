import pandas as pd
import os.path
import json

from utils.ai_utils import perform_chat_completion
from utils.json_utils import compare_dicts
from prompt_templates.system_prompts import get_product_mapping_agent_system_prompt

def get_product_recommendations(user_requirements: dict) -> pd.DataFrame:
    compared_products = perform_products_comparison(user_requirements)
    df_recommendations = compared_products.head(3)
    df_recommendations = df_recommendations[df_recommendations['recommendation_score'] >= 2]
    return df_recommendations

def perform_products_comparison(source_profile: dict) -> pd.DataFrame:
    df = get_available_products()
    df['recommendation_score'] = df['laptop_feature_map'].apply(lambda x: compare_dicts(source_profile, json.loads(x)))
    df_sorted = df.sort_values(by='recommendation_score', ascending=False)
    return df_sorted

def get_available_products() -> pd.DataFrame:
    laptop_data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'laptop_data.csv')
    df = pd.read_csv(laptop_data_file_path)
    
    # check if the 'laptop_feature_map' column exists
    if 'laptop_feature_map' not in df.columns:
        df['laptop_feature_map'] = df['Description'].apply(lambda x: perform_product_mapping(x).replace("```json", '').replace("```", '').strip())

    # check if there are any missing values in the 'laptop_feature_map' column and apply mapping only to those rows
    missing_feature_mask = df['laptop_feature_map'].isnull() | (df['laptop_feature_map'] == '')
    if missing_feature_mask.any():
        df.loc[missing_feature_mask, 'laptop_feature_map'] = df.loc[missing_feature_mask, 'Description'].apply(lambda x: perform_product_mapping(x).replace("```json", '').replace("```", '').strip())
    
    return df

def perform_product_mapping(laptop_description: str) -> str:
    messages = [
        {"role": "system", "content": get_product_mapping_agent_system_prompt(laptop_description)},
        {"role": "user", "content": "Follow the above instructions step-by-step and output the JSON format response as specified."}
    ]
    return perform_chat_completion(messages)