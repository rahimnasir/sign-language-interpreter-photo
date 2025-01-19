import streamlit as st
import requests
import logging
from ultralytics import YOLO
from PIL import Image
import cv2
import numpy as np

BASE_API_URL = "https://9f33-2001-e68-542f-aca1-4400-a20-2bdd-b6fa.ngrok-free.app"  # Update with your actual LangFlow API base URL
FLOW_ID = "78287719-c459-48f1-84ed-db8473f0b34a"

TRAINED_MODEL_PATH = "best.pt"  # Replace with your actual model path

# Initialize logging
logging.basicConfig(level=logging.INFO)

def run_flow(input_message: str) -> str:
    """
    Send the detected gestures list to the LangFlow chatbot API.

    :param input_message: The input message (list of gestures) to send to the chatbot
    :return: The chatbot's response
    """
    api_url = f"{BASE_API_URL}/api/v1/run/{FLOW_ID}"
    payload = {
        "input_value": input_message,
        "output_type": "chat",
        "input_type": "chat"
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        chatbot_response = response.json()
        # Extract the chatbot's message
        return chatbot_response['outputs'][0]['outputs'][0]['results']['message']['text']
    except requests.RequestException as e:
        logging.error(f"Error calling LangFlow API: {e}")
        return "Error connecting to the chatbot."
    except KeyError:
        logging.error("Unexpected API response format.")
        return "Error retrieving chatbot response."

def main():
    # Initialize gesture list in session state
    if "gesture_list" not in st.session_state:
        st.session_state["gesture_list"] = []

    with st.sidebar:
        enable = st.checkbox("Enable camera")
        picture = st.camera_input("Take a picture", disabled=not enable)

        if picture is not None:
            # Convert the uploaded file to an image
            image = Image.open(picture)

            # Convert PIL image to OpenCV format
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Perform inference on the uploaded image
            model = YOLO(TRAINED_MODEL_PATH)
            results = model(image_cv)

            # Draw bounding boxes and process detections
            for result in results:
                detections = result.boxes
                for box in detections:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    confidence = box.conf[0]  # Confidence score
                    class_id = int(box.cls[0])  # Class index
                    class_name = model.names[class_id]  # Class name

                    # Append detected gesture to the session state list if unique
                    if class_name not in st.session_state["gesture_list"]:
                        st.session_state["gesture_list"].append(class_name)

                    # Draw bounding boxes and labels
                    cv2.rectangle(image_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"{class_name} ({confidence:.2f})"
                    cv2.putText(image_cv, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Convert back to RGB for Streamlit display
            image_with_predictions = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
            st.image(image_with_predictions, caption="Predicted Image", use_container_width=True)

    # Display the list of detected gestures
    st.header("Sign Language Interpreter Bot (Photo Version)")
    if st.session_state["gesture_list"]:
        # Join the gesture words with a space to form a readable string
        formatted_gestures = ", ".join(st.session_state["gesture_list"])
        with st.chat_message("user"):
            st.write("Detected words:",formatted_gestures)
    else:
        st.write("No gestures detected yet.")

    # Send the gesture list to the chatbot
    if st.session_state["gesture_list"]:
        input_message = ", ".join(st.session_state["gesture_list"])
        chatbot_output = run_flow(input_message)
        with st.chat_message("assistant"):
            st.write(chatbot_output)

if __name__ == "__main__":
    main()