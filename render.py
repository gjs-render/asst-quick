from flask import Flask, jsonify, request
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create assistant only once for efficiency
assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a personal math tutor. Write and run code to answer math questions.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4o",
)

# Define a route to solve math questions
@app.route('/solve', methods=['POST'])
def solve_equation():
    try:
        # Get the user question from the request JSON
        user_question = request.json.get("question", "")
        
        # Create a thread for the conversation
        thread = client.beta.threads.create()
        
        # Send the user's math question to the assistant
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_question
        )

        # Run the assistant with the instructions
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Please address the user as Jane Doe. The user has a premium account."
        )
        
        # Check the run status and return the messages if completed
        if run.status == 'completed': 
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            return jsonify({"status": "success", "messages": messages}), 200
        else:
            return jsonify({"status": "pending", "run_status": run.status}), 202
    
    except OpenAIError as e:
        logging.error(f"OpenAI Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logging.error(f"Server Error: {str(e)}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500

# Define a health check route for Render
@app.route('/')
def index():
    return "Math Tutor Flask app is running!"

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
