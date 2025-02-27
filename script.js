// Tự động cập nhật nội dung lên ô nhập khi bấm vào câu hỏi phổ biến
document.addEventListener("DOMContentLoaded", function () {
    let buttons = document.querySelectorAll(".marquee-button");
    buttons.forEach(button => {
        button.addEventListener("click", function () {
            let question = this.innerText;
            let inputBox = document.querySelector("input[type='text']");
            if (inputBox) {
                inputBox.value = question;
                inputBox.dispatchEvent(new Event("input", { bubbles: true }));
            }
        });
    });
});