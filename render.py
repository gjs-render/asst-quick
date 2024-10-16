from flask import Flask, render_template, request, jsonify
from openai import OpenAI, OpenAIError
from openai import AssistantEventHandler
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# OpenAI API setup
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Global assistant instance
assistant = None

def initialize_assistant():
    global assistant
    if assistant is None:
        assistant = client.beta.assistants.create(
            name="Math Tutor",
            instructions="You are a personal math tutor. Write and run code to answer math questions.",
            model="gpt-4o"
        )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    # Initialize assistant as needed
    initialize_assistant()

    try:
        user_input = request.json.get('input')
        if not user_input:
            return jsonify({'error': 'Input is required'}), 400
        
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        response_message = []

        class EventHandler(AssistantEventHandler):
            def on_text_created(self, text) -> None:
                logging.info(f"on_text_created: {text.value}")
                response_message.append(text.value)  # Convert to string

            def on_text_delta(self, delta, snapshot):
                logging.info(f"on_text_delta: {delta.value}")
                response_message.append(delta.value)  # Convert to string
            
            def on_tool_call_created(self, tool_call):
                logging.info(f"Tool call created: {tool_call.type}")

            def on_tool_call_delta(self, delta, snapshot):
                if delta.type == 'code_interpreter':
                    if delta.code_interpreter.input:
                        logging.info(f"Interpreter input: {delta.code_interpreter.input}")
                        response_message.append(delta.code_interpreter.input)
                    if delta.code_interpreter.outputs:
                        logging.info("Interpreter outputs:")
                        for output in delta.code_interpreter.outputs:
                            if output.type == "logs":
                                logging.info(output.logs)
                                response_message.append(output.logs)

        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            event_handler=EventHandler()
        ) as stream:
            stream.until_done()

        return jsonify({'response': ''.join(response_message).strip()})
    
    except OpenAIError as e:
        logging.error(f"OpenAI error occurred: {e}")
        return jsonify({'error': 'An error occurred while communicating with OpenAI.'}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
