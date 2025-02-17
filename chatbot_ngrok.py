from flask import Flask, request, jsonify
import wikipediaapi
from underthesea import word_tokenize
from pyngrok import ngrok

app = Flask(__name__)

wiki_wiki = wikipediaapi.Wikipedia(
    user_agent="MyChatbot/1.0 (contact: thanghd1112@gmail.com)",  
    language="vi"
)

def search_wikipedia(query):
    """Tìm kiếm các đoạn văn liên quan đến câu hỏi trên Wikipedia."""
    page = wiki_wiki.page(query)
    if not page.exists():
        return None, None

    paragraphs = page.text.split("\n\n")
    related_paragraphs = [p for p in paragraphs if query.lower() in p.lower()]
    if not related_paragraphs:
        related_paragraphs = [paragraphs[0]]

    return related_paragraphs[:3], page.fullurl

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message", "").strip()
    tokenized = word_tokenize(user_message, format="text")
    related_paragraphs, source_url = search_wikipedia(user_message)

    if related_paragraphs:
        response = f"📌 **{user_message}**\n\n"
        for i, para in enumerate(related_paragraphs, 1):
            response += f"🔹 **Thông tin {i}:** {para}\n\n"
        response += f"🔗 [Xem chi tiết tại Wikipedia]({source_url})"
    else:
        response = "Không tìm thấy thông tin trên Wikipedia."

    return jsonify({"question": user_message, "tokens": tokenized, "response": response})

if __name__ == '__main__':
    # Mở ngrok để tạo link truy cập từ Internet
    public_url = ngrok.connect(5000).public_url
    print(f"Chatbot đang chạy tại: {public_url}")

    app.run(debug=True)
