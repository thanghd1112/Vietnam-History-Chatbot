import streamlit as st
import json
import random

# Load CSS
with open("style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load JavaScript
js_code = """
<script src="static/script.js"></script>
"""
st.markdown(js_code, unsafe_allow_html=True)

st.title("🤖 Chatbot Lịch Sử Việt Nam")
st.write("Nhập câu hỏi và chatbot sẽ giúp bạn tìm hiểu lịch sử!")

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

user_input = st.text_input("Bạn:", st.session_state.user_input)

# Load danh sách câu hỏi từ file JSON
with open("data/popular_questions.json", encoding="utf-8") as f:
    all_popular_questions = json.load(f)

# Lấy ngẫu nhiên 3 câu hỏi từ danh sách lớn
popular_questions = random.sample(all_popular_questions, min(3, len(all_popular_questions)))

st.write("---")
st.write("🔥 **Top những câu được hỏi:**")

# Chia thành 3 cột
cols = st.columns(3)

for i, (col, question) in enumerate(zip(cols, popular_questions)):
    with col:
        html_code = f"""
        <button class="marquee-button" onclick="sendQuestion('{question}')">
            <span>{question}</span>
        </button>
        """
        st.markdown(html_code, unsafe_allow_html=True)

        # Xử lý sự kiện khi bấm vào câu hỏi
        if st.button(question, key=f"top_{i}"):
            st.session_state.user_input = question
            st.rerun()
