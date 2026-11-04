"use client";

import { FormEvent, useEffect, useState } from "react";

type Job = { id: number; query: string; location: string; status: string; created_at: string };

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [health, setHealth] = useState<"checking" | "online" | "offline">("checking");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function refresh() {
    try {
      const [h, j] = await Promise.all([
        fetch(`${API}/health`, { cache: "no-store" }),
        fetch(`${API}/api/search-jobs`, { cache: "no-store" }),
      ]);
      if (!h.ok || !j.ok) throw new Error("API unavailable");
      setHealth("online");
      setJobs(await j.json());
    } catch {
      setHealth("offline");
    }
  }

  useEffect(() => { refresh(); }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (query.trim().length < 3) { setMessage("Please enter at least 3 characters."); return; }
    setBusy(true); setMessage("");
    try {
      const response = await fetch(`${API}/api/search-jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), location: location.trim() }),
      });
      if (!response.ok) throw new Error("Could not save search");
      setQuery(""); setMessage("Search requirement saved. Discovery connectors will be added in a later phase.");
      await refresh();
    } catch {
      setMessage("Backend not reachable. Start the FastAPI server first.");
    } finally { setBusy(false); }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brandmark">TDJ</div>
        <div><div className="brand">THE DIGITAL JUNCTION</div><div className="subbrand">LEAD INTELLIGENCE</div></div>
        <span className={`status ${health}`}>{health === "online" ? "API CONNECTED" : health === "offline" ? "API OFFLINE" : "CHECKING API"}</span>
      </header>

      <section className="hero">
        <div className="eyebrow">UNIVERSAL LEAD DISCOVERY PLATFORM · PHASE 1</div>
        <h1>Find your next<br /><span>opportunity.</span></h1>
        <p>Describe the leads you want to discover. Your search requirements are saved locally and ready for the discovery engine.</p>
      </section>

      <section className="panel">
        <div className="panelhead"><div><div className="eyebrow">NEW SEARCH</div><h2>What are you looking for?</h2></div><span className="localtag">LOCAL-FIRST</span></div>
        <form onSubmit={submit}>
          <label htmlFor="query">Describe your requirement</label>
          <textarea id="query" value={query} onChange={e => setQuery(e.target.value)} placeholder="Example: Find newly opened restaurants in Barasat that may need billing software..." rows={4} />
          <label htmlFor="location">Target location (optional)</label>
          <input id="location" value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g. Barasat, Kolkata, India" />
          <button disabled={busy || health !== "online"}>{busy ? "Saving..." : "Save Search Requirement"}</button>
          {message && <p className="message">{message}</p>}
        </form>
      </section>

      <section className="panel">
        <div className="panelhead"><div><div className="eyebrow">WORKSPACE</div><h2>Recent search requirements</h2></div><button className="refresh" onClick={refresh}>Refresh</button></div>
        {jobs.length === 0 ? <div className="empty">No search requirements yet. Create your first one above.</div> :
          <div className="jobs">{jobs.map(job => <article className="job" key={job.id}><div><strong>{job.query}</strong><p>{job.location || "Location not specified"} · {new Date(job.created_at).toLocaleString()}</p></div><span>{job.status}</span></article>)}</div>}
      </section>
      <footer>TDJ LEAD INTELLIGENCE · BUILT FOR THE DIGITAL JUNCTION · PHASE 1 FOUNDATION</footer>
    </main>
  );
}
