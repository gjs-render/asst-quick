from flask import Flask, request, jsonify
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

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
        logging.info("POST /solve request received")
        
        # Ensure the request contains JSON and a 'question'
        if not request.json or 'question' not in request.json:
            logging.warning("No question provided in the request.")
            return jsonify({"status": "error", "message": "No question provided."}), 400
        
        # Get the user's math question from the request
        user_question = request.json['question']
        logging.info(f"User's question: {user_question}")
        
        # Create a thread for the conversation
        thread = client.beta.threads.create()
        logging.info(f"Created thread: {thread.id}")
        
        # Send the user's question to the assistant
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_question
        )
        logging.info(f"Message sent to assistant: {message.content}")
        
        # Run the assistant with the instructions
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Please address the user as Jane Doe. The user has a premium account."
        )
        logging.info(f"Run status: {run.status}")
        
        # Check if the run is completed
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            logging.info("Run completed successfully.")
            
            # Extract the text content from the messages and return as JSON
            response_content = [msg['content'] for msg in messages if 'content' in msg]
            return jsonify({"status": "success", "messages": response_content}), 200
        else:
            logging.warning(f"Run status: {run.status}")
            return jsonify({"status": "pending", "run_status": run.status}), 202
    
    except OpenAIError as e:
        logging.error(f"OpenAI Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logging.error(f"Server Error: {str(e)}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
