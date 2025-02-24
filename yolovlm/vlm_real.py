from openai import OpenAI
import os
import base64


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_desc(image_path):
    base64_image = encode_image(image_path)
    client = OpenAI(
        # If the environment variable is not configured, please replace the following line with: api_key="sk-xxx",
        api_key='',
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-vl-max",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                    {"type": "text", "text": '''You are an advanced AI model for vehicle accident recognition. Analyze the given image and determine if an accident has occurred. Your response must follow this format:

1. Start with either **"There is an accident"** if an accident is detected, or **"No accident"** if no accident is found.
2. If an accident is detected, describe the vehicles involved, including their types (car, motorcycle, truck, or bus).
3. Provide details about the accident, such as the position of vehicles, potential collision points, and the severity if possible.
4. If no accident is detected, simply state "No accident."

**Example Outputs:**

- **If an accident is detected:**  
  _"There is an accident. A car and a motorcycle have collided at an intersection. The car's front is damaged, and the motorcycle is lying on its side."_  

- **If no accident is detected:**  
  _"No accident."_

### **Additional Guidelines:**
- If multiple vehicles are involved, list them clearly.
- If visibility is unclear, mention "Limited visibility, accident detection uncertain."
- Keep the response concise and factual.
'''},
                ],
            }
        ],
    )
    return completion.choices[0].message.content