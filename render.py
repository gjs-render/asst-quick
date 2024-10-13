from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Added for CORS support
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    # Extract user input from the request
    user_input = request.json.get('input')
    if not user_input:
        return jsonify({'error': 'Input is required'}), 400  # Handle missing input

    try:
        # Log the user input
        logging.info(f"User input: {user_input}")
        
        # Create assistant
        assistant = client.beta.assistants.create(
            name="Math Tutor",
            instructions="You are a personal math tutor. Write and run code to answer math questions.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o",
        )

        # Log assistant creation
        logging.info(f"Assistant created: {assistant.id}")

        # Create a new thread
        thread = client.beta.threads.create()

        # Log thread creation
        logging.info(f"Thread created: {thread.id}")

        # Send the user message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Log that message was sent
        logging.info("Message sent to the assistant.")

        # Capture the assistant's response
        response_message = ""
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Please address the user as Jane Doe. The user has a premium account."
        ) as stream:
            for delta in stream:
                if hasattr(delta, 'content'):
                    response_message += delta.content
                    logging.info(f"Received delta content: {delta.content}")

        # Check if a response was captured
        if response_message.strip():
            logging.info(f"Final response: {response_message.strip()}")
            return jsonify({'response': response_message.strip()})
        else:
            logging.error("No response received from assistant.")
            return jsonify({'error': 'No response received from assistant.'}), 500

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

