from flask import Flask, request, jsonify, render_template
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging
import time  # Import time for sleep functionality

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
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    try:
        # Log the incoming request
        logging.info("Received request to /solve")
        data = request.json
        logging.info(f"Request data: {data}")

        # Check if the question is provided
        if not data or 'question' not in data:
            logging.warning("No question provided in the request.")
            return jsonify({"status": "error", "message": "No question provided."}), 400

        question = data['question']
        logging.info(f"Received question: {question}")

        # Create a thread for the assistant
        thread = client.beta.threads.create()

        # Send the user's message to the assistant
        message = client.beta.threads.messages.create(
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
            response = messages.data[-1].content  # Get the last message content
            logging.info(f"Assistant response: {response}")
            return jsonify({"response": response, "status": "success"})
        else:
            logging.warning("No messages found from the assistant.")
            return jsonify({"response": "No response from assistant.", "status": "success"})

    except OpenAIError as e:
        logging.error(f"OpenAI Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
