## Test with Postman 

from flask import Flask, request, jsonify
import wikipediaapi
from underthesea import word_tokenize

app = Flask(__name__)

# Cấu hình Wikipedia API với User-Agent hợp lệ
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent="VietnamHistoryBot/1.0 (thanghd1112@gmail.com)", 
    language="vi"
)

def search_wikipedia(query):
    """Tìm kiếm nội dung trên Wikipedia, lấy nhiều đoạn văn khác nhau."""
    page = wiki_wiki.page(query)

    if not page.exists():
        return None, None

    # Lấy nội dung trang và chia thành từng đoạn văn
    content = page.text.split("\n\n")  # Tách thành các đoạn riêng biệt
    filtered_content = [para for para in content if len(para) > 100]  # Bỏ đoạn quá ngắn

    return filtered_content[:3], page.fullurl  # Lấy 3 đoạn đầu tiên

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """API nhận câu hỏi và trả về câu trả lời từ Wikipedia."""
    user_message = request.json.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Vui lòng nhập câu hỏi."}), 400

    # Xử lý từ khóa bằng Underthesea
    keywords = word_tokenize(user_message, format="text")

    # Lấy dữ liệu từ Wikipedia
    response_list, source_url = search_wikipedia(user_message)

    if response_list:
        reply = f"**Câu hỏi:** {user_message}\n\n"
        for i, paragraph in enumerate(response_list, start=1):
            reply += f"**Đoạn {i}:** {paragraph}...\n\n"
        reply += f"🔗 [Xem chi tiết tại Wikipedia]({source_url})"
    else:
        reply = f"Xin lỗi, tôi không tìm thấy thông tin về '{user_message}' trên Wikipedia tiếng Việt."

    return jsonify({"response": reply})

if __name__ == '__main__':
    app.run(debug=True)
