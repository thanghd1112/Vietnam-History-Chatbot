import streamlit as st
import requests
import random

# Load file CSS với encoding UTF-8
with open("style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Giao diện chatbot
st.title("🤖 Chatbot với Flask API")
st.write("Nhập tin nhắn của bạn và chatbot sẽ trả lời!")

# Dùng session_state để cập nhật câu hỏi khi bấm gợi ý
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Hộp nhập tin nhắn
user_input = st.text_input("Bạn:", st.session_state.user_input)

# Danh sách câu hỏi phổ biến
popular_questions = [
    "Chiến thắng Điện Biên Phủ là gì?",
    "Nguyên nhân cuộc chiến tranh Đông Dương?",
    "Hậu quả của chiến tranh Đông Dương?",
    "Lý do Mỹ tham gia chiến tranh Việt Nam?",
    "Những điểm chính trong Hiệp định Paris?",
    "Ai là Tổng tư lệnh Quân đội nhân dân Việt Nam trong kháng chiến?",
]

# Xử lý câu trả lời chatbot
related_questions = []
if user_input:
    response = requests.post("http://127.0.0.1:5000/chat", json={"message": user_input})

    if response.status_code == 200:
        bot_reply = response.json().get("response", "Lỗi! Không nhận được phản hồi.")
        st.text_area("Chatbot:", bot_reply, height=100)

        # Dự đoán câu hỏi liên quan dựa trên nội dung hỏi
        if "Điện Biên Phủ" in user_input:
            related_questions = [
                "Ai là chỉ huy trong chiến dịch Điện Biên Phủ?",
                "Ý nghĩa chiến thắng Điện Biên Phủ?",
                "Thời gian diễn ra chiến dịch này?"
            ]
        elif "chiến tranh" in user_input:
            related_questions = [
                "Các giai đoạn chính của chiến tranh Việt Nam?",
                "Tác động của chiến tranh đến nền kinh tế Việt Nam?",
                "Sự kiện nào đánh dấu sự kết thúc chiến tranh?"
            ]
        elif "Mỹ" in user_input:
            related_questions = [
                "Mỹ rút khỏi Việt Nam khi nào?",
                "Chiến dịch Linebacker II là gì?",
                "Tại sao Mỹ không thể chiến thắng ở Việt Nam?"
            ]

        # Hiển thị câu hỏi liên quan
        if related_questions:
            st.write("🔍 **Câu hỏi liên quan:**")
            for q in related_questions:
                if st.button(q, key=f"related_{q}"):
                    st.session_state.user_input = q
                    st.experimental_rerun()  # Làm mới trang ngay lập tức

# Hiển thị "Top những câu được hỏi"
st.write("---")  # Đường kẻ ngang
st.write("🔥 **Top những câu được hỏi:**")

cols = st.columns(len(popular_questions[:3]))  # Chia thành 3 cột ngang
random.shuffle(popular_questions)  # Xáo trộn câu hỏi

for i, question in enumerate(popular_questions[:3]):  # Chọn 3 câu ngẫu nhiên
    with cols[i]:
        if st.button(question, key=f"top_{i}", help="Bấm để hỏi"):
            st.session_state.user_input = question
            st.experimental_rerun()  # Làm mới trang ngay lập tức
