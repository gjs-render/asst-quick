from flask import Flask, request, jsonify
from openai import OpenAI, OpenAIError
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

# Create assistant (initialization can be moved to a route if needed)
assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a personal math tutor. Write and run code to answer math questions.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4"
)

@app.route('/solve', methods=['POST'])
def solve():
    try:
        # Get user input from request
        user_input = request.json.get('input')
        if not user_input:
            return jsonify({'error': 'Input is required'}), 400
        
        # Create a new thread for the user input
        thread = client.beta.threads.create()

        # Send the user message to the assistant
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Event handler for handling assistant responses
        class EventHandler:
            def on_text_created(self, text):
                print(f"\nassistant > {text}", end="", flush=True)
            @override
            def on_text_delta(self, delta, snapshot):
                print(delta.value, end="", flush=True)

            def on_tool_call_created(self, tool_call):
                print(f"\nassistant > {tool_call.type}\n", flush=True)

            def on_tool_call_delta(self, delta, snapshot):
                if delta.type == 'code_interpreter':
                    if delta.code_interpreter.input:
                        print(delta.code_interpreter.input, end="", flush=True)
                    if delta.code_interpreter.outputs:
                        print(f"\n\noutput >", flush=True)
                        for output in delta.code_interpreter.outputs:
                            if output.type == "logs":
                                print(f"\n{output.logs}", flush=True)
                                
        response_message = ""
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            event_handler=EventHandler()
        ) as stream:
            stream.until_done()
        
        return jsonify({'response': response_message.strip()})

    except OpenAIError as e:
        logging.error(f"OpenAI error occurred: {e}")
        return jsonify({'error': 'An error occurred while communicating with OpenAI.'}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

if __name__ == '__main__':
    # Run the app on the specified port (Render uses port 5000 by default)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
