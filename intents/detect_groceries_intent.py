import base64
import requests
import os
import dotenv
from langchain_core.tools import tool


@tool("detect_groceries")
def detect_groceries_tool():
    """Use this tool when asked to scan the cupboard or to scan the purchase. Do not use it when asked fi specific items are available. It captures an image and will return a list of detected groceries in the image. Read the number and each product separately."""
    return process()

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def process():
    # Replace this URL with the actual URL of your ESP32 camera server
    url = 'http://10.42.0.64/capture'
    # Path to your image
    image_path = "./pictures/captured_image.jpg"
    dotenv.load_dotenv()

    # OpenAI API Key
    api_key = os.getenv('OPENAI_API_KEY')
    # Sending a GET request to the ESP32-CAM and saving the response
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Open a file in binary write mode and save the image
        if os.path.exists(image_path):
            # Remove the file
            os.remove(image_path)
            print(f"The file {image_path} has been deleted.")
        with open(image_path, 'wb') as f:
            f.write(response.content)
        print("Image saved successfully.")
    else:
        print("Failed to retrieve the image.")

    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4o",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "Name the groceries and how many there are in the image each in 1 word."
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # print(response.choices[0].message.content)
    return response.json()["choices"][0]["message"]["content"]