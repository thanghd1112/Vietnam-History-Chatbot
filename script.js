// Khi người dùng bấm vào câu hỏi, nó sẽ cập nhật input box
function sendQuestion(question) {
    var inputBox = window.parent.document.querySelector('input[type="text"]');
    if (inputBox) {
        inputBox.value = question;
        inputBox.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Tự động gửi bằng cách giả lập sự kiện "Enter"
        setTimeout(() => {
            var enterKeyEvent = new KeyboardEvent('keydown', {
                bubbles: true, cancelable: true, keyCode: 13
            });
            inputBox.dispatchEvent(enterKeyEvent);
        }, 300);
    }
}
