from flask import Flask, request, jsonify
from underthesea import word_tokenize, pos_tag, text_normalize
import json
import re
import unicodedata
import logging
from difflib import SequenceMatcher
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class HistoryBot:
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
        normalized_question = self.normalize_text(user_question)
        keywords = self.extract_keywords(normalized_question)

        candidate_qids = set()
        for keyword in keywords:
            candidate_qids.update(self.keyword_index.get(keyword, []))

        similar_questions = []
        for qid in candidate_qids:
            qa_pair = self.qa_data[qid]
            similarity = SequenceMatcher(None, normalized_question, self.normalize_text(qa_pair["question"])).ratio()
            if similarity >= threshold:
                similar_questions.append((qid, similarity))

        return sorted(similar_questions, key=lambda x: x[1], reverse=True)

    def get_response(self, user_question):
        try:
            similar_questions = self.find_similar_questions(user_question)
            if not similar_questions:
                return {"status": "not_found", "response": "Xin lỗi, tôi không tìm thấy câu trả lời phù hợp."}

            best_match_id, similarity = similar_questions[0]
            qa_pair = self.qa_data[best_match_id]
            response = qa_pair["answer"]

            related_questions = [self.qa_data[qid]["question"] for qid, _ in similar_questions[1:4]]

            return {"status": "success", "response": response, "related_questions": related_questions}

        except Exception as e:
            logging.error(f"Lỗi xử lý câu hỏi: {str(e)}")
            return {"status": "error", "response": "Đã xảy ra lỗi trong quá trình xử lý"}

chatbot = HistoryBot()

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
