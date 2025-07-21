from flask import Flask, request, jsonify, render_template
from chatbot import CaliforniaCybersecurityChatbot

app = Flask(__name__)
chatbot = CaliforniaCybersecurityChatbot()

# Load data and train model
chatbot.load_qa_data()
chatbot.train_model()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_query = request.json.get("question", "")
    if not user_query:
        return jsonify({"error": "Empty question"}), 400
    
    response_data = chatbot.generate_response(user_query)
    return jsonify({
        "answer": response_data["response"],
        "confidence": response_data["confidence"],
        "source": response_data["source"],
        "category": response_data.get("category", "general")
    })

if __name__ == "__main__":
    app.run(debug=True)
