const { useState, useEffect } = React;

const API_BASE = "";

function formatDate(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleTimeString();
}

function MemoryList({ title, subtitle, items, kind }) {
  return (
    <div className="column-card">
      <div className="column-title">{title}</div>
      <div className="column-subtitle">{subtitle}</div>
      {items.length === 0 && (
        <div className="hint">
          No {kind} memories yet. Create an event in the box above and watch this fill in.
        </div>
      )}
      {items.map((m) => (
        <div key={m.id} className="memory-item">
          <div className="memory-content">{m.content}</div>
          <div className="memory-meta">
            <span className="tag">
              <span className="pill">
                {m.type === "episodic" ? "Episodic" : "Knowledge"}
              </span>
            </span>
            <span>Mentions: {m.mentions}</span>
            <span>Trust: {m.trust.toFixed(2)}</span>
            <span>Created: {formatDate(m.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function App() {
  const [content, setContent] = useState("");
  const [ttl, setTtl] = useState(60);
  const [episodic, setEpisodic] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchMemories = async () => {
    try {
      const [eRes, kRes] = await Promise.all([
        fetch(`${API_BASE}/memory/episodic`),
        fetch(`${API_BASE}/memory/knowledge`),
      ]);
      const eData = await eRes.json();
      const kData = await kRes.json();
      setEpisodic(eData);
      setKnowledge(kData);
    } catch (err) {
      console.error(err);
      setError("Failed to load memories from backend.");
    }
  };

  useEffect(() => {
    fetchMemories();
    const id = setInterval(fetchMemories, 2000);
    return () => clearInterval(id);
  }, []);

  const submit = async () => {
    if (!content.trim()) return;
    setLoading(true);
    setError("");
    try {
      await fetch(`${API_BASE}/memory/write`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: content.trim(),
          ttl_seconds: Number(ttl) || 60,
        }),
      });
      setContent("");
      fetchMemories();
    } catch (err) {
      console.error(err);
      setError("Failed to write memory.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="app">
      <div className="card">
        <div className="title">Self Evolving Shared Memory Fabric</div>
        <div className="subtitle">
          A lightweight cognitive memory layer for multi agent systems. Create events, watch them
          appear as episodic memories, then see them promote into long term knowledge when
          reinforced.
        </div>
        <div className="input-row">
          <input
            placeholder='Example: "door is open" or "user prefers Japanese responses"'
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <input
            style={{ maxWidth: 80 }}
            type="number"
            min="5"
            max="600"
            value={ttl}
            onChange={(e) => setTtl(e.target.value)}
            title="TTL in seconds for episodic memory"
          />
          <button onClick={submit} disabled={loading}>
            {loading ? "Saving..." : "Add event"}
          </button>
        </div>
        <div className="hint">
          TTL controls how long episodic memories live before decaying. Repeating the same content
          twice within about 2 minutes promotes it into knowledge.
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      <div className="columns">
        <MemoryList
          title="Episodic Memory"
          subtitle="Short lived situational events with TTL and decay."
          items={episodic}
          kind="episodic"
        />
        <MemoryList
          title="Knowledge Memory"
          subtitle="Consolidated high trust facts promoted from repeated episodic events."
          items={knowledge}
          kind="knowledge"
        />
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
