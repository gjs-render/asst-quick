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
            return jsonify({"status": "success", "messages": [msg.content for msg in messages]}), 200
        else:
            logging.warning(f"Run status: {run.status}")
            return jsonify({"status": "pending", "run_status": run.status}), 202
    
    except OpenAIError as e:
        logging.error(f"OpenAI Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logging.error(f"Server Error: {str(e)}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500
