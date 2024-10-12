from flask import Flask, request, jsonify
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging

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
    return "Math Tutor Flask app is running!"

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

        # Run the Assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=assistant_id
    )

    # Check if the Run requires action (function call)
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run.id
        )
        print(f"Run status: {run_status.status}")
        if run_status.status == "completed":
            break
        sleep(1)  # Wait for a second before checking again

    # Retrieve and return the latest message from the assistant
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value

    print(f"Assistant response: {response}")
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
