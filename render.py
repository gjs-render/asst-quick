from flask import Flask, render_template, request, jsonify
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

@app.route('/submit', methods=['POST'])
def handle_submit():
    data = request.form['data']
    return f"Received: {data}"
    
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    user_input = request.json.get('input')
    if not user_input:
        return jsonify({'error': 'Input is required'}), 400  # Handle missing input

    logging.info(f"User input: {user_input}")

    try:
        # Create assistant (only if it doesn't exist)
        assistant_name = "Math Tutor"
        existing_assistants = client.beta.assistants.list()  # Check for existing assistants
        assistant = next((a for a in existing_assistants if a.name == assistant_name), None)
        
        if not assistant:
            assistant = client.beta.assistants.create(
                name=assistant_name,
                instructions="You are a personal math tutor. Write and run code to answer math questions.",
                tools=[{"type": "code_interpreter"}],
                model="gpt-4"
            )
            logging.info(f"Assistant created: {assistant.id}, Tools: {assistant.tools}")
        else:
            logging.info(f"Using existing assistant: {assistant.id}")

        # Create a new thread
        thread = client.beta.threads.create()
        logging.info(f"Thread created: {thread.id}")

        # Send the user message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )
        logging.info("Message sent to the assistant.")

        # Capture the assistant's response
        response_message = ""
        has_received_content = False

        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Please address the user as Jane Doe. The user has a premium account."
        ) as stream:
            logging.info("Started receiving stream from assistant.")
            
            for delta in stream:
                if hasattr(delta, 'content'):
                    logging.info(f"Content found: {delta.content}")
                    response_message += delta.content
                    has_received_content = True
                elif hasattr(delta, 'error'):
                    logging.error(f"Assistant returned an error: {delta.error}")

        if not has_received_content:
            logging.error("No meaningful response received from assistant.")
            return jsonify({'error': 'No response received from the assistant.'}), 500
        
        return jsonify({'response': response_message.strip()})

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
