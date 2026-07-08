import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.error || "Could not sign in. Is the server running?");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center px-4">
      <div className="w-full max-w-sm">
        <p className="font-mono text-accent text-sm mb-1">&gt;_ code-review</p>
        <h1 className="font-mono text-2xl font-bold mb-6">Sign in</h1>

        <div className="bg-panel border border-edge rounded-lg p-6 space-y-4">
          <div>
            <label className="comment-label block mb-1">email</label>
            <input
              className="field"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
          <div>
            <label className="comment-label block mb-1">password</label>
            <input
              className="field"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>

          {error && (
            <p className="text-bad text-sm font-mono">{error}</p>
          )}

          <button className="btn w-full justify-center" onClick={submit} disabled={busy}>
            {busy ? "Signing in..." : "Sign in"}
          </button>
        </div>

        <p className="text-mist text-sm mt-4">
          New here?{" "}
          <Link to="/register" className="text-accent hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
