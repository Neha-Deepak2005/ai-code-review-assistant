import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { useAuth } from "../AuthContext";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // upload form state
  const [mode, setMode] = useState("file"); // "file" | "snippet"
  const [projectName, setProjectName] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef(null);

  const loadProjects = async () => {
    try {
      const { data } = await api.get("/upload/projects");
      setProjects(data.projects);
    } catch {
      setError("Could not load projects. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadProjects(); }, []);

  const submit = async () => {
    setError("");
    if (!projectName.trim()) { setError("Give the project a name first."); return; }
    setBusy(true);
    try {
      if (mode === "file") {
        const files = fileRef.current?.files;
        if (!files || files.length === 0) {
          setError("Choose at least one .py file.");
          setBusy(false);
          return;
        }
        const form = new FormData();
        form.append("project_name", projectName);
        for (const f of files) form.append("files", f);
        await api.post("/upload/file", form);
        fileRef.current.value = "";
      } else {
        if (!code.trim()) { setError("Paste some code first."); setBusy(false); return; }
        await api.post("/upload/snippet", { project_name: projectName, code });
        setCode("");
      }
      setProjectName("");
      await loadProjects();
    } catch (err) {
      setError(err.response?.data?.error || "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!confirm("Delete this project and all its reviews?")) return;
    await api.delete(`/upload/projects/${id}`);
    loadProjects();
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* header */}
      <header className="flex items-center justify-between mb-10">
        <div>
          <p className="font-mono text-accent text-sm">&gt;_ code-review</p>
          <h1 className="font-mono text-xl font-bold">Dashboard</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-mist text-sm">{user?.name}</span>
          <button className="btn-ghost" onClick={() => { logout(); navigate("/login"); }}>
            Sign out
          </button>
        </div>
      </header>

      {/* upload card */}
      <section className="bg-panel border border-edge rounded-lg p-6 mb-10">
        <p className="comment-label mb-4">new review</p>

        <div className="flex gap-2 mb-4">
          <button
            className={mode === "file" ? "btn" : "btn-ghost"}
            onClick={() => setMode("file")}
          >
            Upload .py files
          </button>
          <button
            className={mode === "snippet" ? "btn" : "btn-ghost"}
            onClick={() => setMode("snippet")}
          >
            Paste code
          </button>
        </div>

        <div className="space-y-4">
          <input
            className="field"
            placeholder="Project name"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
          />

          {mode === "file" ? (
            <input
              ref={fileRef}
              type="file"
              accept=".py"
              multiple
              className="block text-sm text-mist file:mr-3 file:btn file:border-0"
            />
          ) : (
            <textarea
              className="field font-mono h-44 resize-y"
              placeholder={"def hello():\n    print('paste your Python here')"}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              spellCheck={false}
            />
          )}

          {error && <p className="text-bad text-sm font-mono">{error}</p>}

          <button className="btn" onClick={submit} disabled={busy}>
            {busy ? "Uploading..." : "Create project"}
          </button>
        </div>
      </section>

      {/* project list */}
      <section>
        <p className="comment-label mb-4">projects</p>

        {loading ? (
          <p className="text-mist text-sm font-mono">Loading...</p>
        ) : projects.length === 0 ? (
          <div className="border border-dashed border-edge rounded-lg p-10 text-center">
            <p className="text-mist">No projects yet. Upload a .py file above to run your first review.</p>
          </div>
        ) : (
          <ul className="space-y-2">
            {projects.map((p) => (
              <li
                key={p.id}
                className="bg-panel border border-edge rounded-lg px-4 py-3
                           flex items-center justify-between hover:border-mist transition"
              >
                <div>
                  <p className="font-medium">{p.project_name}</p>
                  <p className="font-mono text-xs text-mist">
                    #{p.id} · {p.upload_type === "snippet" ? "pasted snippet" : "file upload"} ·{" "}
                    {new Date(p.created_at).toLocaleDateString()} · {p.review_count} review(s)
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    className="btn-ghost"
                    onClick={() => navigate(`/projects/${p.id}`)}
                  >
                    Open
                  </button>
                  <button className="btn-ghost hover:!text-bad" onClick={() => remove(p.id)}>
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
