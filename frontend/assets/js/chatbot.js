
const API_URL = "/chatbot/chat";

document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chatWindow");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const toggleButton = document.getElementById("chatToggleButton");
    const closeButton = document.getElementById("chatCloseButton");

    if (
        !chatWindow ||
        !chatForm ||
        !chatInput ||
        !chatMessages ||
        !toggleButton ||
        !closeButton
    ) {
        return;
    }

    const sendButton = chatForm.querySelector('button[type="submit"]');

    function setChatOpen(open) {
        chatWindow.classList.toggle("hidden", !open);
        chatWindow.classList.toggle("flex", open);

        if (open) {
            chatInput.focus();
        }
    }

    toggleButton.addEventListener("click", () => {
        const isOpen = !chatWindow.classList.contains("hidden");
        setChatOpen(!isOpen);
    });

    closeButton.addEventListener("click", () => {
        setChatOpen(false);
    });

    function addChatMessage(text, sender) {
        const message = document.createElement("div");

        if (sender === "user") {
            message.className =
                "bg-brand-navy text-white p-3 rounded-lg rounded-tr-none " +
                "text-sm self-end max-w-[85%] shadow-sm " +
                "whitespace-pre-wrap break-words";
        } else {
            message.className =
                "bg-white p-3 rounded-lg rounded-tl-none " +
                "border border-gray-200 text-sm text-gray-700 " +
                "self-start max-w-[85%] shadow-sm " +
                "whitespace-pre-wrap break-words";
        }

        message.textContent = text;

        chatMessages.appendChild(message);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return message;
    }

    chatForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const question = chatInput.value.trim();

        if (!question) {
            return;
        }

        addChatMessage(question, "user");

        chatInput.value = "";
        chatInput.disabled = true;

        if (sendButton) {
            sendButton.disabled = true;
        }

        const loadingMessage = addChatMessage(
            "Searching guidelines...",
            "bot"
        );

        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "The chatbot request failed."
                );
            }

            const answer = data.answer || "No answer was returned.";

            if (window.marked && window.DOMPurify) {
                loadingMessage.classList.remove("whitespace-pre-wrap");
                loadingMessage.classList.add("bot-markdown");

                loadingMessage.innerHTML = window.DOMPurify.sanitize(
                    window.marked.parse(answer)
                );
            } else {
                loadingMessage.textContent = answer;
            }

        } catch (error) {
            console.error("CDVH RAG chatbot error:", error);

            loadingMessage.textContent =
                "Unable to contact the chatbot. Please check that " +
                "FastAPI and Ollama are running.";

        } finally {
            chatInput.disabled = false;

            if (sendButton) {
                sendButton.disabled = false;
            }

            chatInput.focus();
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });
});
