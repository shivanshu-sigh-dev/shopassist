import json

from flask import Flask
from flask import render_template, request, jsonify

from utils import ai_utils, json_utils 
from prompt_templates.system_prompts import get_requirements_capture_system_prompt, get_conversation_classifier_agent_system_prompt, get_product_detail_extractor_agent_system_prompt
from prompt_templates.user_prompts import get_product_detail_extractor_agent_user_prompt
from product_mapping.product_mapping_agent import get_product_recommendations, get_available_products
from product_details.product_details_agent import fetch_product_details


app = Flask(__name__)
user_requirements_conversation = [
    {"role": "system", "content": get_requirements_capture_system_prompt()}
]
product_details_conversation = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat")
def chat():
    user_message = request.args.get('text', '')
    response = get_response_for_user_message(user_message)
    
    # Returen response
    callback = request.args.get('callback', False)
    if callback:
        # Wrap the response in the callback function for JSONP
        return f"{callback}({jsonify(response).get_data(as_text=True)})"
    else:
        # Return regular JSON if no callback is provided
        return jsonify(response)
    
def conversation_stage_classifier() -> bool:
    classifier_messages = [
        {"role": "system", "content": get_conversation_classifier_agent_system_prompt()},
        {"role": "user", "content": "Conversation history: ```json " + json.dumps(user_requirements_conversation) + " ```"}
    ]
    classification_response = ai_utils.perform_chat_completion(classifier_messages)
    print("Conversation Stage Classification Response:", classification_response)
    return "true" in classification_response

def product_details_extractor(user_message: str) -> str:
    product_details_conversation.append(
        {"role": "user", "content": get_product_detail_extractor_agent_user_prompt(user_message)}
    )
    details_extractor_response = ai_utils.perform_chat_completion(product_details_conversation)
    product_details_conversation.append({"role": "assistant", "content": details_extractor_response})
    return details_extractor_response

def get_product_recommendations_response(user_requirements: dict) -> str:
    df_recommendations = get_product_recommendations(user_requirements)
    df_recommendations = df_recommendations.drop(columns=['laptop_feature', 'recommendation_score', 'Description', 'Special Features', 'Clock Speed', 'OS', 'Average Battery Life', 'Storage Type', 'Display Type', 'Screen Resolution', 'Warranty'])
    product_details_conversation.append(
        {"role": "system", "content": get_product_detail_extractor_agent_system_prompt(', '.join(df_recommendations.apply(lambda row: f"{row['Brand']} {row['Model Name']}", axis=1).tolist()))},
    )
    html_table = df_recommendations.to_html(classes="table-striped", index=False)
    return f"Based on your requirements, here are the top laptop recommendations:<br>{html_table}"

def get_response_for_user_message(user_message: str) -> dict:
    if ai_utils.perform_moderation_check(user_message):
        response = {"output": [{"type": "text", "value": "Your message was flagged by moderation filter."}]}
    else:
        user_requirements_conversation.append({"role": "user", "content": user_message})
        is_intent_clarification_stage = conversation_stage_classifier()
        if is_intent_clarification_stage:
            # Conversation is regarding capturing laptop requirements
            ai_response = ai_utils.perform_chat_completion(user_requirements_conversation)
            user_requirements_conversation.append({"role": "assistant", "content": ai_response})
            if json_utils.is_strict_json_object(ai_response):
                # Capturing laptop requirements completed
                json_string = ai_response.replace("```json", '').replace("```", '').strip()
                response_text = get_product_recommendations_response(json.loads(json_string))
                user_requirements_conversation.append({"role": "assistant", "content": response_text})
                response = {"output": [{"type": "text", "value": response_text}]}
            else:
                response = {"output": [{"type": "text", "value": ai_response}]}
        else:
            # Conversation is regarding the recommended products
            product_detail_response = product_details_extractor(user_message)
            if json_utils.is_strict_json_object(product_detail_response):
                product_detail_answer = fetch_product_details(user_message, get_available_products())
                response = {"output": [{"type": "text", "value": product_detail_answer}]}
            else:
                response = {"output": [{"type": "text", "value": product_detail_response}]}
    
    return response
