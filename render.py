from flask import Flask, request, jsonify, render_template
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging
import time

# Load environment variables
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create a Flask application
app = Flask(__name__)

# Create the assistant once when the app starts
assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a personal math tutor. Your job is to solve mathematical equations and explain the solutions.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4o",
)

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    """Handle the POST request to solve a math question."""
    try:
        data = request.json

        if not data or 'question' not in data:
            return jsonify({"status": "error", "message": "No question provided."}), 400

        question = data['question']
        logging.info(f"Received question: {question}")

        # Create a thread for the assistant
        thread = client.beta.threads.create()

        # Send the user's message to the assistant
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        # Run the assistant and wait for completion
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # Poll the run status
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            logging.info(f"Run status: {run_status.status}")
            if run_status.status == "completed":
                break
            time.sleep(1)  # Wait for a second before checking again

        # Retrieve and return the latest message from the assistant
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        # Ensure we are accessing the correct content
        if messages.data:
            last_message = messages.data[-1]  # Get the last message object
            if hasattr(last_message, 'content'):
                response = last_message.content  # This should be a string
                logging.info(f"Assistant response: {response}")
                return jsonify({"response": response, "status": "success"})
            else:
                logging.error("Last message does not have 'content'.")
                return jsonify({"response": "No valid content in response.", "status": "error"})
        else:
            logging.warning("No messages found from the assistant.")
            return jsonify({"response": "No response from assistant.", "status": "success"})

    except OpenAIError as e:
        logging.error(f"OpenAI Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500
