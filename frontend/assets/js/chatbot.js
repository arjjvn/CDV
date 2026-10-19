
const API_URL = "/chatbot/chat";

document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chatWindow");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const toggleButton = document.getElementById("chatToggleButton");
    const closeButton = document.getElementById("chatCloseButton");

    // This page might not contain the chatbot.
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

    // Open or close the chat window.
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

    // Display a message in the chat window.
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

        // Render the content as text rather than HTML.
        message.textContent = text;

        chatMessages.appendChild(message);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return message;
    }

    // Send the user's question to FastAPI.
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
            "Searching disaster-management guidelines...",
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

            loadingMessage.textContent =
                data.answer || "No answer was returned.";

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
