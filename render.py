from flask import Flask, request, jsonify
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create the assistant
assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a personal math tutor. Write and run code to answer math questions.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4o",
)

@app.route('/')
def index():
    return "Math Tutor Flask app is running!"

@app.route('/solve', methods=['POST'])
def solve_equation():
    try:
        logging.info("POST /solve route accessed.")  # Debugging log
        
        # Ensure the request contains JSON and a 'question'
        if not request.json or 'question' not in request.json:
            logging.warning("No question provided in the request.")
            return jsonify({"status": "error", "message": "No question provided."}), 400
        
        # Log the incoming question
        logging.info(f"Received question: {request.json['question']}")
        
        # Get the question from the request
        user_question = request.json['question']
        
        # Create a new thread and post a message
        thread = client.beta.threads.create()
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_question
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Please address the user as Jane Doe. The user has a premium account."
        )
        
        # If run completed, get the messages
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            response_content = [msg['content'] for msg in messages if 'content' in msg]
            return jsonify({"status": "success", "messages": response_content}), 200
        else:
            return jsonify({"status": "pending", "run_status": run.status}), 202
    
    except OpenAIError as e:
        logging.error(f"OpenAI Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logging.error(f"Server Error: {str(e)}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500

# Run the app on the port provided by Render
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # Use the port specified by Render
    app.run(host='0.0.0.0', port=port)
