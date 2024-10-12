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
        data = request.json
        question = data.get('question', '')
        logging.info(f"Received question: {question}")

        # Create a thread for the assistant
        thread = client.beta.threads.create()

        # Send the user's message to the assistant
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        # Run the assistant
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Please address the user as Jane Doe. The user has a premium account."
        )

        # Check the run status
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            response_content = [msg['content'] for msg in messages if 'content' in msg]
            logging.info(f"Messages from assistant: {response_content}")

            # If there are no messages, return a helpful message
            if not response_content:
                return jsonify({"status": "success", "messages": ["No response from assistant."]}), 200
            
            return jsonify({"status": "success", "messages": response_content}), 200
        else:
            logging.warning(f"Run status: {run.status}")
            return jsonify({"status": "failure", "messages": ["Assistant did not complete the request."]}), 400

    except OpenAIError as e:
        logging.error(f"OpenAI error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
