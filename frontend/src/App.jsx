import { useEffect, useState } from "react";
import "./App.css";
import GraphView from "./GraphView";



function extractEntityIds(evidence = []) {
  const ids = new Set();

  function scan(value) {
    if (!value) return;

    if (typeof value === "string") return;

    if (Array.isArray(value)) {
      value.forEach(scan);
      return;
    }

    if (typeof value === "object") {
      Object.entries(value).forEach(([key, item]) => {
        if (
          typeof item === "string" &&
          (key === "id" || key.endsWith("_id")) &&
          /^(sys|person|team|decision|incident|doc|project|technology)_[a-z0-9_]+$/i.test(item)
        ) {
          ids.add(item);
        }

        scan(item);
      });
    }
  }

  scan(evidence);
  return [...ids];
}

function extractDependencyPath(evidence = []) {
  const paths = [];

  for (const item of evidence) {
    if (item.tool !== "blast_radius") continue;

    const result = item.result;
    if (!result?.found || !result.target_system?.system_id) continue;

    const target = result.target_system.system_id;

    const affected = [...(result.affected_systems || [])].sort(
      (a, b) => a.dependency_depth - b.dependency_depth
    );

    paths.push({
      target,
      affected: affected.map((system) => ({
        id: system.system_id,
        depth: system.dependency_depth,
      })),
    });
  }

  return paths;
}



const API = "http://127.0.0.1:8000";

const actions = [
  {
    id: "owner",
    label: "System ownership",
    description: "Who owns a system?",
    placeholder: "sys_payment_gateway",
  },
  {
    id: "experts",
    label: "Find experts",
    description: "Find people with relevant experience",
    placeholder: "Payment Modernization",
  },
  {
    id: "blast",
    label: "Blast radius",
    description: "Explore downstream dependencies",
    placeholder: "sys_payment_gateway",
  },
];

const suggestions = [
  "Who currently owns the Payment Gateway, and who owned it previously?",
  "If the Payment Gateway fails, which systems could be affected?",
  "Who has experience resolving payment incidents?",
  "What changed in system ownership during July 2026?",
];

export default function App() {
  const [active, setActive] = useState("chat");
  const [input, setInput] = useState("sys_payment_gateway");
  const [depth, setDepth] = useState("5");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState("Checking connection");

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [focusIds, setFocusIds] = useState([]);
  const [dependencyPaths, setDependencyPaths] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  async function checkHealth() {
    try {
      const response = await fetch(`${API}/api/health`);
      if (!response.ok) throw new Error("Backend unavailable");
      await response.json();
      setHealth("Connected");
    } catch {
      setHealth("Disconnected");
    }
  }

  useEffect(() => {
    checkHealth();
  }, []);

  async function runQuery(event) {
    event?.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      let url;

      if (active === "owner") {
        url = `${API}/api/owner/${encodeURIComponent(input.trim())}`;
      } else if (active === "experts") {
        url = `${API}/api/experts?topic=${encodeURIComponent(input.trim())}`;
      } else {
        url = `${API}/api/blast-radius/${encodeURIComponent(input.trim())}?max_depth=${depth}`;
      }

      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Request failed");
      }

      setResult(data);
    } catch (err) {
      setError(`${err.message}. Check that the FastAPI backend is running.`);
    } finally {
      setLoading(false);
      checkHealth();
    }
  }

  async function sendMessage(event, suppliedQuestion) {
    event?.preventDefault();

    const text = (suppliedQuestion ?? question).trim();
    if (!text || chatLoading) return;

    setQuestion("");
    setChatError("");
    setChatLoading(true);

    setMessages((previous) => [
      ...previous,
      { role: "user", content: text },
    ]);

    try {
      const response = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "The AI request failed.");
      }

      
      const evidence = data.evidence || [];

      setFocusIds(extractEntityIds(evidence));
      setDependencyPaths(extractDependencyPath(evidence));

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer || "The agent returned no answer.",
          evidence,
          model: data.model || "Unknown model",
        },
      ]);

    } catch (err) {
      setChatError(
        `${err.message} Check that the FastAPI backend is running and /api/chat is available.`
      );
    } finally {
      setChatLoading(false);
      checkHealth();
    }
  }

  function selectAction(action) {
    setActive(action.id);
    setInput(action.placeholder);
    setResult(null);
    setError("");
  }

  function startNewChat() {
    setMessages([]);
    setQuestion("");
    setChatError("");
    setActive("chat");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">N</div>
          <div>
            <strong>Company Brain</strong>
            <span>KNOWLEDGE INTELLIGENCE</span>
          </div>
        </div>

        <div className="side-label">WORKSPACE</div>

        <button
          className={`nav-item ${active === "chat" ? "selected" : ""}`}
          onClick={() => setActive("chat")}
        >
          <span className="nav-dot" />
          AI Chat
        </button>

        {actions.map((action) => (
          <button
            key={action.id}
            className={`nav-item ${active === action.id ? "selected" : ""}`}
            onClick={() => selectAction(action)}
          >
            <span className="nav-dot" />
            {action.label}
          </button>
        ))}
        
        <button
          className={`nav-item ${active === "graph" ? "selected" : ""}`}
          onClick={() => setActive("graph")}
        >
          <span className="nav-dot" />
          Knowledge Graph
        </button>


        {active === "chat" && (
          <button className="new-chat-button" onClick={startNewChat}>
            + New conversation
          </button>
        )}

        <div className="sidebar-bottom">
          <div className={`status-dot ${health === "Connected" ? "online" : ""}`} />
          <div>
            <strong>{health}</strong>
            <span>FalkorDB · API status</span>
          </div>
          <button
            className="refresh"
            onClick={checkHealth}
            title="Check connection"
          >
            ↻
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="breadcrumb">NovaTech /</span>{" "}
            {active === "chat" ? "AI Assistant" : "Intelligence workspace"}
          </div>
          <span className="environment">DEMO ENVIRONMENT</span>
        </header>

        <section className={`welcome ${active === "graph" ? "graph-welcome" : ""}`}>
          <div className="eyebrow">COMPANY KNOWLEDGE GRAPH</div>
          <h1>
            {active === "chat"
              ? "Ask your company anything."
              : "Understand how your company works."}
          </h1>
          <p>
            Explore company knowledge, trace dependencies, find experienced
            teammates, and investigate decisions using evidence from the
            connected knowledge graph.
          </p>
        </section>

        {active === "graph" ? (
          <section className="graph-section">
            <GraphView
              focusIds={focusIds}
              dependencyPaths={dependencyPaths}
            />
          </section>
        ) : active === "chat" ? (
          <section className="chat-panel">
            <div className="chat-header">
              <div>
                <span className="eyebrow">AI INVESTIGATION AGENT</span>
                <h2>Company Brain Assistant</h2>
              </div>
              <span className="live-label">
                <span /> GRAPH CONNECTED
              </span>
            </div>

            <div className="chat-messages">
              {messages.length === 0 && (
                <div className="chat-empty">
                  <div className="empty-icon">✳</div>
                  <h3>Your company's knowledge, connected.</h3>
                  <p>
                    Ask a question in plain English. The agent uses graph tools
                    to investigate and returns the evidence behind its answer.
                  </p>

                  <div className="suggestion-list">
                    {suggestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        className="suggestion-button"
                        onClick={() => sendMessage(null, suggestion)}
                        disabled={chatLoading}
                      >
                        <span>{suggestion}</span>
                        <span aria-hidden="true">↗</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((message, index) => (
                <article
                  key={`${index}-${message.role}`}
                  className={`chat-message ${message.role}`}
                >
                  <div className="message-label">
                    {message.role === "user" ? "YOU" : "COMPANY BRAIN"}
                  </div>

                  <div className="message-content">{message.content}</div>

                  {message.role === "assistant" && (
                    <div className="message-meta">
                      <details className="evidence-details">
                        <summary>
                          Evidence used ({message.evidence?.length || 0} tool
                          calls)
                        </summary>
                        {message.evidence?.length ? (
                          <div className="evidence-list">
                            {message.evidence.map((item, evidenceIndex) => (
                              <details
                                className="evidence-item"
                                key={`${item.tool}-${evidenceIndex}`}
                              >
                                <summary>{item.tool}</summary>
                                <pre>
                                  {JSON.stringify(
                                    {
                                      arguments: item.arguments,
                                      result: item.result,
                                    },
                                    null,
                                    2
                                  )}
                                </pre>
                              </details>
                            ))}
                          </div>
                        ) : (
                          <p className="no-evidence">
                            No tool evidence was returned for this answer.
                          </p>
                        )}
                      </details>
                      <span className="model-label">
                        Model: {message.model}
                      </span>
                    </div>
                  )}
                </article>
              ))}

              {chatLoading && (
                <div className="chat-message assistant">
                  <div className="message-label">COMPANY BRAIN</div>
                  <div className="message-content thinking">
                    Investigating the knowledge graph…
                  </div>
                </div>
              )}

              {chatError && (
                <div className="error-state">
                  <strong>Message failed</strong>
                  <p>{chatError}</p>
                  <button
                    className="copy-button"
                    onClick={() => {
                      const lastUserMessage = [...messages]
                        .reverse()
                        .find((message) => message.role === "user");
                      if (lastUserMessage) {
                        sendMessage(null, lastUserMessage.content);
                      }
                    }}
                    disabled={chatLoading}
                  >
                    Retry request
                  </button>
                </div>
              )}
            </div>

            <form
              className="chat-form"
              onSubmit={(event) => sendMessage(event)}
            >
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about ownership, incidents, decisions, or dependencies…"
                rows={2}
                maxLength={2000}
                disabled={chatLoading}
                aria-label="Ask Company Brain a question"
              />
              <div className="chat-form-bottom">
                <span>Answers are grounded in available graph evidence.</span>
                <button
                  className="run-button"
                  type="submit"
                  disabled={chatLoading || !question.trim()}
                >
                  {chatLoading ? "Investigating…" : "Ask Company Brain ↗"}
                </button>
              </div>
            </form>
          </section>
        ) : (
          <section className="workspace">
            <div className="query-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">INTELLIGENCE TOOLS</span>
                  <h2>Investigate your company</h2>
                </div>
                <span className="tool-count">03 TOOLS</span>
              </div>

              <div className="action-grid">
                {actions.map((action, index) => (
                  <button
                    key={action.id}
                    className={`action-card ${
                      active === action.id ? "active-card" : ""
                    }`}
                    onClick={() => selectAction(action)}
                  >
                    <span className="action-number">0{index + 1}</span>
                    <strong>{action.label}</strong>
                    <span>{action.description}</span>
                  </button>
                ))}
              </div>

              <form onSubmit={runQuery} className="query-form">
                <label htmlFor="query-input">
                  {active === "experts" ? "TOPIC OR PROJECT" : "SYSTEM ID"}
                </label>
                <input
                  id="query-input"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Enter a query..."
                  required
                />

                {active === "blast" && (
                  <div className="depth-control">
                    <label htmlFor="depth">MAXIMUM DEPENDENCY DEPTH</label>
                    <select
                      id="depth"
                      value={depth}
                      onChange={(event) => setDepth(event.target.value)}
                    >
                      {[1, 2, 3, 4, 5].map((n) => (
                        <option key={n} value={n}>
                          {n} level{n > 1 ? "s" : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <button
                  className="run-button"
                  disabled={loading || !input.trim()}
                >
                  {loading ? "Investigating..." : "Run investigation →"}
                </button>
              </form>
            </div>

            <div className="result-panel">
              <div className="result-header">
                <div>
                  <span className="eyebrow">GRAPH RESPONSE</span>
                  <h2>Investigation results</h2>
                </div>
                <span className="live-label">
                  <span /> LIVE
                </span>
              </div>

              {!result && !error && !loading && (
                <div className="empty-state">
                  <div className="empty-icon">⌘</div>
                  <h3>Ready to investigate</h3>
                  <p>
                    Choose a tool, enter a system ID or topic, and run your
                    first query.
                  </p>
                  <button
                    onClick={() => {
                      setActive("owner");
                      setInput("sys_payment_gateway");
                    }}
                  >
                    Try system ownership →
                  </button>
                </div>
              )}

              {loading && (
                <div className="message-state">
                  Traversing the knowledge graph...
                </div>
              )}

              {error && (
                <div className="error-state">
                  <strong>Investigation failed</strong>
                  <p>{error}</p>
                </div>
              )}

              {result && (
                <div className="result-content">
                  <div className="result-summary">
                    <span>QUERY STATUS</span>
                    <strong>
                      {result.found ? "Evidence found" : "Query completed"}
                    </strong>
                  </div>
                  <pre>{JSON.stringify(result, null, 2)}</pre>
                  <button
                    className="copy-button"
                    onClick={() =>
                      navigator.clipboard.writeText(
                        JSON.stringify(result, null, 2)
                      )
                    }
                  >
                    Copy evidence JSON
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        <footer>
          <span>COMPANY BRAIN · NOVATECH</span>
          <span>Evidence-backed intelligence · FalkorDB</span>
        </footer>
      </main>
    </div>
  );
}
