// Placeholder for now — on Day 7 this becomes the full report view
// with severity badges, metrics cards, and charts.

import { useParams, Link } from "react-router-dom";

export default function ProjectDetail() {
  const { id } = useParams();

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link to="/" className="text-accent text-sm hover:underline">&larr; Back to dashboard</Link>
      <h1 className="font-mono text-xl font-bold mt-4">Project #{id}</h1>
      <div className="border border-dashed border-edge rounded-lg p-10 text-center mt-6">
        <p className="text-mist">
          The analysis report view is coming on Day 7 — run reviews via Postman until then.
        </p>
      </div>
    </div>
  );
}
