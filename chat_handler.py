# chat_handler.py
import os
import uuid
from bucket_operations import upload_image_to_gcs
from vertexai.generative_models import (
    GenerativeModel,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
    Part,
)

from config import load_config
from llm_tools import tools, get_functions
import streamlit as st
from PIL import Image
import io

def get_safety_config():
    safety_config = [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
    return safety_config

def get_llm_response(prompt, chat, model=None):
    if model is not None:
        chat = model.start_chat()
    safety_config = get_safety_config()
    try:
        response = chat.send_message(prompt, safety_settings=safety_config)
    except Exception as e:
        return
    return response


def submit_message(config, uploaded_file):
    """
    Handles the submission of a user message and processes the LLM response.
    """

    user_input = st.session_state.get("user_input", "").strip()
    if not user_input:
        return
    prompt = ["You have access to tools to add pins on a map and update the status of zones. "
              "First, decide the appropriate action based on the input:\n\n"
              "If the input describes an event (excluding search-related updates), determine its approximate location using the best available information, categorize it as either a 'collision' or 'robbery,' and add a pin to the map.\n"
              "If there is an update directly related to Marina - update the file with volunteers insights. For instance someone has found something that belongs to her or saw somewhere. Do not use ' signs when you rephrase the update.\n"
              "If the input indicates that a search has started or finished, update the zone status with one of the following: 'Available,' 'In Progress,' or 'Searched.'. List of the available zones will be specified further in the prompt. Make sure that you select the zone from the list. In case person is going to search the part of the specific zone - ask to search the full zone.\n"
              "For inquiries or inputs that require no action: Respond naturally to the user without using any tools.\n"
              "Act accordingly without asking follow-up questions. Always provide some text as output. User input:\n" + user_input + "\n Based on all the information you know provide the recommendations regarding the next steps for the search.\n"
              "The available zones are: " + str(st.session_state.zones) + "\nUpdates:" + str(st.session_state['person_updates']) +
              "\n The text response should be purely in natural language format even if the tool was used."]

    st.session_state["my_file_uploader"] = None
    # Append user message to chat history
    if uploaded_file:
        image = Image.open(io.BytesIO(uploaded_file.read()))
        #vertex_image = VertexImage.load_from_file(image)
        unique_id = str(uuid.uuid4())
        # Example usage for file naming
        file_name = f"{unique_id}.png"
        blob =  'images' + os.sep + file_name
        upload_image_to_gcs('missing_people_search', image, blob)
        #prompt.append(Part.from_image(VertexImage.load_from_file("/Users/npoly/Desktop/backpack.png")))
        prompt.append(Part.from_uri(uri=f"gs://missing_people_search/{blob}", mime_type="image/png"))
        st.session_state.messages.append({"is_user": True, "text": user_input, "image": image})
    else:
        st.session_state.messages.append({"is_user": True, "text": user_input})

    # Initialize the LLM model
    try:
        model = GenerativeModel(
            model_name=config.get("llm_id", "gemini-1.5-pro"), tools=[tools]
        )
    except Exception as e:
        st.error(f"Failed to initialize LLM model: {e}")
        return

    if "chat" not in st.session_state:
        st.session_state["chat"] = model.start_chat(response_validation=False)

    try:
        response = get_llm_response(prompt, st.session_state["chat"])
        parts = response.candidates[0].content.parts
    except AttributeError as e:
        st.error(f"An error occurred: {e}")

    print(response)

    # Process the LLM response
   

    function_call = None
    for part in parts:
        if hasattr(part, 'function_call') and part.function_call:
            function_call = part.function_call
            break

    functions = get_functions()

    if function_call and function_call.name in functions:
        function_name = function_call.name
        function_args = function_call.args

        if function_args:
            try:
                function_response = functions[function_name](**function_args)
                # Send function response back to LLM
                response = st.session_state["chat"].send_message(
                    Part.from_function_response(
                        name=function_name,
                        response={"content": function_response},
                    )
                )
                # Collect text from all parts
                bot_response = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if hasattr(part, 'text') and part.text
                )
            except Exception as e:
                bot_response = f"Error executing function '{function_name}': {e}"
        else:
            bot_response = "No arguments provided for the function."
    else:
        # Collect text from all parts
        bot_response = "".join(
            part.text for part in parts
            if hasattr(part, 'text') and part.text
        )
    print(bot_response)
    #Append bot response to chat history
    if user_input == 'hi gemini' and 'pending_news' in st.session_state and st.session_state["pending_news"]:
        st.session_state['pending_news'] = False
        st.session_state['last_green'] = True

        update = """There is a new update: A person clinging to a cliff has been successfully rescued by helicopter.\n
The incident occurred near Baker Beach. While the rescue was successful, it is recommended to visit the location to ensure the rescued individual is safe and to verify if the person is Marina, as part of the ongoing search efforts."""
        st.session_state.messages.append({"is_user": False, "text": update})
        print(st.session_state.messages)
    else:
        st.session_state.messages.append({"is_user": False, "text": bot_response})
    st.session_state.user_input = ""  # Clear input field
    st.session_state['last_green'] = False
