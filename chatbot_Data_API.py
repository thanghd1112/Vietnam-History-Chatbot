from flask import Flask, request, jsonify
import json
import re
import unicodedata
import logging
from difflib import SequenceMatcher
from collections import defaultdict
from underthesea import word_tokenize, pos_tag, text_normalize
import openai
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from flask_cors import CORS
import os


app = Flask(__name__)
CORS(app)  # Cho phép cross-origin requests
logging.basicConfig(level=logging.INFO)

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Cấu hình OpenAI API (thay YOUR_API_KEY bằng key của bạn)
openai.api_key = os.getenv("OPENAI_API_KEY")

class EnhancedHistoryBot:
    def __init__(self):
        self.qa_data = self.load_json_data("data/qa_history_data.json")
        self.response_patterns = self.load_json_data("data/response_patterns.json")
        self.keyword_index = self.build_keyword_index()
        
    def load_json_data(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Không tìm thấy file {file_path}")
            return {}

    def build_keyword_index(self):
        keyword_index = defaultdict(list)
        for qid, qa_pair in self.qa_data.items():
            keywords = self.extract_keywords(qa_pair["question"])
            for keyword in keywords:
                keyword_index[keyword].append(qid)
        return keyword_index

    def normalize_text(self, text):
        text = text_normalize(text)
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    def extract_keywords(self, text):
        text = self.normalize_text(text)
        pos_tags = pos_tag(text)
        important_words = [word for word, tag in pos_tags if tag.startswith(("N", "Np", "V"))]
        return important_words

    def find_similar_questions(self, user_question, threshold=0.6):
        """
        Tìm các câu hỏi tương tự trong cơ sở dữ liệu.
        
        Args:
            user_question (str): Câu hỏi của người dùng
            threshold (float): Ngưỡng độ tương đồng (0.0 - 1.0)
            
        Returns:
            list: Danh sách các tuple (question_id, similarity_score)
        """
        normalized_question = self.normalize_text(user_question)
        keywords = self.extract_keywords(normalized_question)
        
        # Tìm các câu hỏi có chứa từ khóa
        candidate_qids = set()
        for keyword in keywords:
            candidate_qids.update(self.keyword_index.get(keyword, []))
        
        # Tính điểm tương đồng cho mỗi câu hỏi ứng viên
        similar_questions = []
        for qid in candidate_qids:
            qa_pair = self.qa_data[qid]
            stored_question = qa_pair["question"]
            
            # Tính điểm tương đồng dựa trên từ khóa
            keyword_similarity = len(set(keywords) & set(self.extract_keywords(stored_question))) / len(set(keywords))
            
            # Tính điểm tương đồng dựa trên chuỗi
            string_similarity = SequenceMatcher(None, 
                                             normalized_question, 
                                             self.normalize_text(stored_question)).ratio()
            
            # Kết hợp hai điểm số (có thể điều chỉnh trọng số)
            combined_similarity = (keyword_similarity * 0.4 + string_similarity * 0.6)
            
            if combined_similarity >= threshold:
                similar_questions.append((qid, combined_similarity))
        
        # Sắp xếp theo độ tương đồng giảm dần
        return sorted(similar_questions, key=lambda x: x[1], reverse=True)

    def get_response(self, user_question):
        try:
            # Bước 1: Tìm kiếm trong dữ liệu có sẵn
            similar_questions = self.find_similar_questions(user_question, threshold=0.6)
            
            if similar_questions:
                # Nếu tìm thấy câu trả lời trong dữ liệu có sẵn
                best_match_id, similarity = similar_questions[0]
                qa_pair = self.qa_data[best_match_id]
                response = qa_pair["answer"]
                
                # Thêm thông tin về độ tương đồng và nguồn
                confidence_info = "🎯 Độ tương đồng: {:.0%}".format(similarity)
                if "sources" in qa_pair:
                    sources_info = "\n\n📚 Nguồn tham khảo: " + ", ".join(qa_pair["sources"])
                else:
                    sources_info = ""
                
                complete_response = f"{response}\n\n{confidence_info}{sources_info}"
                
                related_questions = [
                    self.qa_data[qid]["question"] 
                    for qid, sim in similar_questions[1:4]
                ]
                
                return {
                    "status": "success",
                    "response": complete_response,
                    "related_questions": related_questions,
                    "source": "local_database"
                }
            
            # Bước 2: Tìm kiếm từ OpenAI
            openai_response = self.query_openai(user_question)
            if openai_response:
                return {
                    "status": "success",
                    "response": openai_response,
                    "source": "openai",
                    "related_questions": []
                }
            
            # Bước 3: Tìm kiếm từ Google
            google_results = self.search_google(user_question)
            if google_results:
                response = "Dựa trên các nguồn tin cậy trên internet:\n\n"
                for result in google_results:
                    response += f"📌 {result['snippet']}\n"
                    response += f"🔗 Nguồn: {result['link']}\n\n"
                
                return {
                    "status": "success",
                    "response": response,
                    "source": "google",
                    "related_questions": []
                }
            
            return {
                "status": "not_found",
                "response": "Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn.",
                "related_questions": []
            }

        except Exception as e:
            logging.error(f"Lỗi xử lý câu hỏi: {str(e)}")
            return {
                "status": "error",
                "response": "Đã xảy ra lỗi trong quá trình xử lý",
                "related_questions": []
            }

    def query_openai(self, question):
        """Sử dụng OpenAI API để trả lời câu hỏi."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Bạn là một chuyên gia về lịch sử Việt Nam. Hãy trả lời ngắn gọn, chính xác và đưa ra nguồn tham khảo nếu có."},
                    {"role": "user", "content": question}
                ],
                max_tokens=500
            )
            return response.choices[0].message['content']
        except Exception as e:
            logging.error(f"Lỗi khi truy vấn OpenAI: {str(e)}")
            return None

    def get_response(self, user_question):
        try:
            # Bước 1: Tìm kiếm trong dữ liệu có sẵn
            similar_questions = self.find_similar_questions(user_question, threshold=0.6)
            
            if similar_questions:
                # Nếu tìm thấy câu trả lời trong dữ liệu có sẵn
                best_match_id, similarity = similar_questions[0]
                qa_pair = self.qa_data[best_match_id]
                response = qa_pair["answer"]
                related_questions = [self.qa_data[qid]["question"] for qid, _ in similar_questions[1:4]]
                
                return {
                    "status": "success",
                    "response": response,
                    "related_questions": related_questions,
                    "source": "local_database"
                }
            
            # Bước 2: Tìm kiếm từ OpenAI
            openai_response = self.query_openai(user_question)
            if openai_response:
                return {
                    "status": "success",
                    "response": openai_response,
                    "source": "openai",
                    "related_questions": []
                }
            
            # Bước 3: Tìm kiếm từ Google
            google_results = self.search_google(user_question)
            if google_results:
                # Tạo câu trả lời từ kết quả Google
                response = "Dựa trên các nguồn tin cậy trên internet:\n\n"
                for result in google_results:
                    response += f"📌 {result['snippet']}\n"
                    response += f"🔗 Nguồn: {result['link']}\n\n"
                
                return {
                    "status": "success",
                    "response": response,
                    "source": "google",
                    "related_questions": []
                }
            
            return {
                "status": "not_found",
                "response": "Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn.",
                "related_questions": []
            }

        except Exception as e:
            logging.error(f"Lỗi xử lý câu hỏi: {str(e)}")
            return {
                "status": "error",
                "response": "Đã xảy ra lỗi trong quá trình xử lý",
                "related_questions": []
            }

chatbot = EnhancedHistoryBot()

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"status": "error", "message": "Vui lòng nhập câu hỏi"}), 400

        response = chatbot.get_response(user_message)
        return jsonify(response)

    except Exception as e:
        logging.error(f"Lỗi API: {str(e)}")
        return jsonify({"status": "error", "message": "Đã xảy ra lỗi trong quá trình xử lý"}), 500

if __name__ == "__main__":
    app.run(debug=True)