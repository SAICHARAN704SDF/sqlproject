function sendMessage() {
  const input = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");
  const msg = input.value.trim();
  if (!msg) return;

  const userDiv = document.createElement("div");
  userDiv.className = "message user";
  userDiv.textContent = msg;
  chatBox.appendChild(userDiv);
  input.value = "";

  fetch("/get", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ msg })
  })
  .then(res => res.json())
  .then(data => {
    const botDiv = document.createElement("div");
    botDiv.className = "message bot";
    botDiv.textContent = data.response;
    chatBox.appendChild(botDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  })
  .catch(console.error);
}
