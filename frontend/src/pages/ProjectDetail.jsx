// Day 7 — the report view.
//
// Flow: load project -> user clicks "Run analysis" -> POST /reviews/run/:id
// -> backend runs pylint + bandit + radon -> we render score, metrics,
// severity distribution, and the findings table.

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../api";

const SEV_ORDER = ["critical", "high", "medium", "low", "info"];
const SEV_STYLES = {
  critical: "bg-bad/20 text-bad border-bad/40",
  high: "bg-warn/20 text-warn border-warn/40",
  medium: "bg-accent/20 text-accent border-accent/40",
  low: "bg-mist/10 text-mist border-edge",
  info: "bg-mist/10 text-mist border-edge",
};
const SEV_BAR = {
  critical: "bg-bad",
  high: "bg-warn",
  medium: "bg-accent",
  low: "bg-mist",
  info: "bg-edge",
};

function Badge({ sev }) {
  return (
    <span className={`font-mono text-xs border rounded px-1.5 py-0.5 ${SEV_STYLES[sev] || SEV_STYLES.info}`}>
      {sev}
    </span>
  );
}

function ScoreRing({ score }) {
  // simple conic-gradient ring, no chart library needed
  const color = score >= 80 ? "#3fb970" : score >= 50 ? "#d9a13b" : "#e5604c";
  return (
    <div
      className="w-24 h-24 rounded-full grid place-items-center shrink-0"
      style={{ background: `conic-gradient(${color} ${score * 3.6}deg, #262d38 0deg)` }}
    >
      <div className="w-[76px] h-[76px] rounded-full bg-panel grid place-items-center">
        <span className="font-mono text-xl font-bold" style={{ color }}>{score}</span>
      </div>
    </div>
  );
}

export default function ProjectDetail() {
  const { id } = useParams();

  const [project, setProject] = useState(null);
  const [files, setFiles] = useState([]);
  const [review, setReview] = useState(null);   // latest review with findings
  const [metrics, setMetrics] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");  // severity filter

  const load = async () => {
    try {
      const { data } = await api.get(`/upload/projects/${id}`);
      setProject(data.project);
      setFiles(data.files);
      // fetch latest existing review, if any
      const res = await api.get("/reviews/");
      const mine = res.data.reviews.filter((r) => r.project_id === Number(id));
      if (mine.length > 0) {
        const full = await api.get(`/reviews/${mine[0].id}`);
        setReview(full.data.review);
      }
    } catch {
      setError("Could not load this project.");
    }
  };

  useEffect(() => { load(); }, [id]);

  const runAnalysis = async () => {
    setError("");
    setRunning(true);
    try {
      const { data } = await api.post(`/reviews/run/${id}`);
      setReview(data.review);
      setMetrics(data.metrics);
    } catch (err) {
      setError(err.response?.data?.error || "Analysis failed.");
    } finally {
      setRunning(false);
    }
  };

  const findings = review?.findings || [];
  const counts = SEV_ORDER.reduce((acc, s) => {
    acc[s] = findings.filter((f) => f.severity === s).length;
    return acc;
  }, {});
  const shown = filter === "all" ? findings : findings.filter((f) => f.severity === filter);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <Link to="/" className="text-accent text-sm hover:underline">&larr; Back to dashboard</Link>

      <div className="flex items-center justify-between mt-4 mb-8 flex-wrap gap-4">
        <div>
          <h1 className="font-mono text-xl font-bold">{project?.project_name || `Project #${id}`}</h1>
          <p className="font-mono text-xs text-mist mt-1">
            {files.length} file(s): {files.join(", ")}
          </p>
        </div>
        <button className="btn" onClick={runAnalysis} disabled={running}>
          {running ? "Analyzing..." : review ? "Re-run analysis" : "Run analysis"}
        </button>
      </div>

      {error && <p className="text-bad text-sm font-mono mb-6">{error}</p>}

      {running && (
        <div className="border border-edge rounded-lg p-10 text-center">
          <p className="font-mono text-mist animate-pulse">
            Running pylint, bandit and radon...
          </p>
        </div>
      )}

      {!running && !review && !error && (
        <div className="border border-dashed border-edge rounded-lg p-10 text-center">
          <p className="text-mist">No analysis yet. Run one to get a quality report.</p>
        </div>
      )}

      {!running && review && (
        <>
          {/* summary row */}
          <section className="bg-panel border border-edge rounded-lg p-6 mb-6
                              flex items-center gap-6 flex-wrap">
            <ScoreRing score={review.review_score ?? 0} />
            <div className="flex-1 min-w-[240px]">
              <p className="comment-label mb-1">summary</p>
              <p className="text-sm leading-relaxed">{review.summary}</p>
              {metrics && (
                <p className="font-mono text-xs text-mist mt-2">
                  LOC {metrics.loc} · max complexity {metrics.max_complexity} ·
                  maintainability {metrics.maintainability_index ?? "n/a"}/100
                </p>
              )}
            </div>
          </section>

          {/* severity distribution */}
          <section className="bg-panel border border-edge rounded-lg p-6 mb-6">
            <p className="comment-label mb-3">severity distribution</p>
            <div className="flex h-3 rounded overflow-hidden mb-3">
              {SEV_ORDER.map((s) =>
                counts[s] > 0 ? (
                  <div
                    key={s}
                    className={SEV_BAR[s]}
                    style={{ width: `${(counts[s] / findings.length) * 100}%` }}
                    title={`${s}: ${counts[s]}`}
                  />
                ) : null
              )}
            </div>
            <div className="flex gap-4 flex-wrap">
              {SEV_ORDER.map((s) => (
                <button
                  key={s}
                  onClick={() => setFilter(filter === s ? "all" : s)}
                  className={`font-mono text-xs flex items-center gap-1.5
                              ${filter === s ? "text-paper" : "text-mist"} hover:text-paper`}
                >
                  <span className={`w-2 h-2 rounded-sm ${SEV_BAR[s]}`} />
                  {s} ({counts[s]})
                </button>
              ))}
              {filter !== "all" && (
                <button onClick={() => setFilter("all")}
                        className="font-mono text-xs text-accent hover:underline">
                  clear filter
                </button>
              )}
            </div>
          </section>

          {/* findings table */}
          <section className="bg-panel border border-edge rounded-lg overflow-hidden">
            <p className="comment-label p-4 pb-0">
              findings — {shown.length} of {findings.length}
            </p>
            {shown.length === 0 ? (
              <p className="text-mist text-sm p-6">Nothing in this category. 🎉</p>
            ) : (
              <ul className="divide-y divide-edge mt-3">
                {shown.map((f) => (
                  <li key={f.id} className="px-4 py-3">
                    <div className="flex items-start gap-3 flex-wrap">
                      <Badge sev={f.severity} />
                      <span className="font-mono text-xs text-mist mt-0.5">
                        {f.source}{f.line_number ? ` · L${f.line_number}` : ""}
                      </span>
                      <p className="text-sm flex-1 min-w-[200px]">{f.issue}</p>
                    </div>
                    {(f.explanation || f.suggestion) && (
                      <div className="mt-1.5 ml-1 text-xs text-mist space-y-0.5">
                        {f.explanation && <p>{f.explanation}</p>}
                        {f.suggestion && (
                          <p className="text-ok">↳ {f.suggestion}</p>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
