import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Sparkles, MessageCircle } from "lucide-react";
import { sendChatMessage, getResults } from "../api.js";

const SUGGESTED = [
  "What trials are available for lung cancer patients?",
  "Explain ECOG performance status criteria",
  "What does PENDING_DATA verdict mean?",
  "How does the eligibility screening pipeline work?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [resultId, setResultId] = useState(null);
  const [results, setResults] = useState([]);
  const bottomRef = useRef(null);

  useEffect(() => {
    getResults().then(setResults).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text) => {
    if (!text.trim() || loading) return;
    const userMsg = { role: "user", content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const data = await sendChatMessage(text.trim(), resultId, history);
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message || "Failed to get response"}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="px-8 py-5 border-b border-slate-200 bg-white shrink-0">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div>
            <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <MessageCircle className="w-6 h-6 text-teal-600" />
              Ask AI
            </h2>
            <p className="text-slate-500 text-sm mt-1">
              Ask questions about trials, eligibility criteria, or screening results.
            </p>
          </div>
          {results.length > 0 && (
            <select
              value={resultId || ""}
              onChange={(e) => setResultId(e.target.value ? Number(e.target.value) : null)}
              className="text-sm border border-slate-200 rounded-lg px-3 py-2 text-slate-600
                focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
            >
              <option value="">General chat</option>
              {results.map((r) => (
                <option key={r.id} value={r.id}>
                  Result #{r.id} — {r.patient_name} ({r.eligibility})
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && !loading && (
            <div className="text-center py-16">
              <div className="w-16 h-16 rounded-2xl bg-teal-50 flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-teal-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-700 mb-2">TrialScreen AI Assistant</h3>
              <p className="text-sm text-slate-400 mb-8 max-w-md mx-auto">
                I can help you understand clinical trial eligibility criteria, screening results,
                and answer questions about specific patients or trials.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
                {SUGGESTED.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => send(q)}
                    className="text-left px-4 py-3 rounded-xl border border-slate-200 bg-white
                      text-sm text-slate-600 hover:border-teal-300 hover:bg-teal-50
                      hover:text-teal-700 transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-teal-500 inline mr-2" />
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-teal-700" />
                </div>
              )}
              <div
                className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-teal-600 text-white rounded-br-md"
                    : "bg-slate-100 text-slate-700 rounded-bl-md"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-lg bg-slate-200 flex items-center justify-center shrink-0 mt-1">
                  <User className="w-4 h-4 text-slate-600" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4 text-teal-700" />
              </div>
              <div className="bg-slate-100 px-4 py-3 rounded-2xl rounded-bl-md">
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Thinking...
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="px-8 py-4 border-t border-slate-200 bg-white shrink-0">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
            placeholder="Ask about trials, eligibility, or screening results..."
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-xl border border-slate-200 text-sm text-slate-700
              placeholder-slate-400 focus:outline-none focus:border-teal-400 focus:ring-2
              focus:ring-teal-100 disabled:bg-slate-50 disabled:text-slate-400"
          />
          <button
            onClick={() => send(input)}
            disabled={!input.trim() || loading}
            className="px-4 py-3 rounded-xl bg-teal-600 text-white hover:bg-teal-700
              disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
