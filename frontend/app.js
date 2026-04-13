/**
 * Voice Productivity Assistant — Frontend
 *
 * Uses @elevenlabs/client via CDN (ESM import).
 * No build step required.
 *
 * Configuration:
 *   Set AGENT_ID below (or load from a config endpoint).
 */

// ─── Config ───────────────────────────────────────────────────────────────────
// Replace with your ElevenLabs agent ID from the dashboard or create_elevenlabs_agent.py
const AGENT_ID = "agent_0101kkpat0xze7cbjkdps57cwmj4";

// ─── ElevenLabs SDK ───────────────────────────────────────────────────────────
import { Conversation } from "https://esm.sh/@elevenlabs/client@latest";

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const toggleBtn = document.getElementById("toggle-btn");
const btnLabel = document.getElementById("btn-label");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const transcriptContainer = document.getElementById("transcript-container");

// ─── State ────────────────────────────────────────────────────────────────────
let conversation = null;
let isActive = false;

// ─── Status helpers ───────────────────────────────────────────────────────────
const STATUS_LABELS = {
  idle: "Ready",
  connecting: "Connecting…",
  listening: "Listening",
  processing: "Processing…",
  speaking: "Speaking",
  error: "Error",
};

function setStatus(status) {
  statusDot.className = `status-dot ${status}`;
  statusText.textContent = STATUS_LABELS[status] ?? status;
}

// ─── Transcript helpers ───────────────────────────────────────────────────────
function clearTranscriptHint() {
  const hint = transcriptContainer.querySelector(".transcript-hint");
  if (hint) hint.remove();
}

function appendTranscript(speaker, message) {
  clearTranscriptHint();
  const entry = document.createElement("div");
  entry.className = `transcript-entry ${speaker}`;

  const speakerEl = document.createElement("span");
  speakerEl.className = "speaker";
  speakerEl.textContent = speaker === "user" ? "You" : "Assistant";

  const msgEl = document.createElement("p");
  msgEl.className = "message";
  msgEl.textContent = message;

  entry.appendChild(speakerEl);
  entry.appendChild(msgEl);
  transcriptContainer.appendChild(entry);
  transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
}

// ─── Conversation lifecycle ───────────────────────────────────────────────────
async function startConversation() {
  if (!AGENT_ID || AGENT_ID === "YOUR_AGENT_ID_HERE") {
    alert("Please set AGENT_ID in frontend/app.js before starting.");
    return;
  }

  setStatus("connecting");
  toggleBtn.disabled = true;

  try {
    // Request microphone access
    await navigator.mediaDevices.getUserMedia({ audio: true });

    conversation = await Conversation.startSession({
      agentId: AGENT_ID,

      onConnect: () => {
        isActive = true;
        setStatus("listening");
        toggleBtn.classList.add("active");
        btnLabel.textContent = "Stop";
        toggleBtn.disabled = false;
        toggleBtn.setAttribute("aria-label", "Stop conversation");
      },

      onDisconnect: () => {
        isActive = false;
        conversation = null;
        setStatus("idle");
        toggleBtn.classList.remove("active");
        btnLabel.textContent = "Start";
        toggleBtn.disabled = false;
        toggleBtn.setAttribute("aria-label", "Start conversation");
      },

      onError: (error) => {
        console.error("Conversation error:", error);
        setStatus("error");
        appendTranscript("agent", `Error: ${error.message ?? "Unknown error"}`);
      },

      onModeChange: ({ mode }) => {
        // mode: "listening" | "speaking"
        if (isActive) {
          setStatus(mode === "speaking" ? "speaking" : "listening");
        }
      },

      onMessage: ({ source, message }) => {
        if (!isActive) return;
        if (source === "user") {
          appendTranscript("user", message);
        } else if (source === "ai") {
          appendTranscript("agent", message);
          setStatus("speaking");
        }
      },
    });
  } catch (err) {
    console.error("Failed to start conversation:", err);
    setStatus("error");
    toggleBtn.disabled = false;
    toggleBtn.classList.remove("active");
    btnLabel.textContent = "Start";

    if (err.name === "NotAllowedError") {
      appendTranscript("agent", "Microphone access denied. Please allow microphone access and try again.");
    } else {
      appendTranscript("agent", `Failed to connect: ${err.message}`);
    }
  }
}

async function stopConversation() {
  toggleBtn.disabled = true;
  const conv = conversation;
  conversation = null;
  isActive = false;
  if (conv) {
    try {
      await conv.endSession();
    } catch (_) {
      // WebSocket may already be closed — safe to ignore
    }
  }
  setStatus("idle");
  toggleBtn.classList.remove("active");
  btnLabel.textContent = "Start";
  toggleBtn.disabled = false;
}

// ─── Event listeners ──────────────────────────────────────────────────────────
toggleBtn.addEventListener("click", () => {
  if (isActive) {
    stopConversation();
  } else {
    startConversation();
  }
});

// Keyboard shortcut: Space to toggle
document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && e.target === document.body) {
    e.preventDefault();
    toggleBtn.click();
  }
});
