import React, { useEffect, useState } from "react";
import { assignmentApi, ticketsApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import "@/pages/admin/Admin.css";

interface SlaPolicy { priority: string; first_response_minutes: number; resolve_minutes: number; }

export default function ConfigPage() {
  const [algorithms, setAlgorithms] = useState<string[]>([]);
  const [active, setActive] = useState("");
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      assignmentApi.getConfig().then(({ data }) => { setAlgorithms(data.available_algorithms); setActive(data.active_algorithm); }),
      ticketsApi.slaPolicies().then(({ data }) => setPolicies(data)),
    ]).finally(() => setLoading(false));
  }, []);

  const handleAlgorithmChange = async (algorithm: string) => {
    setError("");
    try {
      const { data } = await assignmentApi.setConfig(algorithm);
      setActive(data.active_algorithm);
      setMessage(`Assignment algorithm switched to ${data.active_algorithm}.`);
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not update algorithm.");
    }
  };

  const updatePolicy = (priority: string, field: "first_response_minutes" | "resolve_minutes", value: number) => {
    setPolicies((p) => p.map((pol) => (pol.priority === priority ? { ...pol, [field]: value } : pol)));
  };

  const savePolicy = async (policy: SlaPolicy) => {
    setError("");
    setMessage("");
    try {
      await ticketsApi.updateSlaPolicy(policy.priority, { first_response_minutes: policy.first_response_minutes, resolve_minutes: policy.resolve_minutes });
      setMessage(`SLA policy for ${policy.priority} saved.`);
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not save policy.");
    }
  };

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page" data-testid="config-page">
      <div className="page-header">
        <div>
          <h1>Assignment &amp; SLA Config</h1>
          <p className="text-muted">Choose the active assignment algorithm and tune SLA policies.</p>
        </div>
      </div>

      {message && <div className="settings-success" data-testid="config-success-message">{message}</div>}
      {error && <div className="form-error" data-testid="config-error-message">{error}</div>}

      <div className="card config-section">
        <h3>Assignment algorithm</h3>
        <div className="config-algorithm-options">
          {algorithms.map((a) => (
            <label key={a} className={`config-algorithm-option ${a === active ? "config-algorithm-option-active" : ""}`}>
              <input type="radio" name="algorithm" value={a} checked={a === active} data-testid={`config-algorithm-${a}`} onChange={() => handleAlgorithmChange(a)} />
              {a.replace("_", " ")}
            </label>
          ))}
        </div>
      </div>

      <div className="card config-section">
        <h3>SLA policies (minutes)</h3>
        <div className="table-wrapper">
          <table className="data-table">
            <thead><tr><th>Priority</th><th>First response</th><th>Resolve</th><th></th></tr></thead>
            <tbody>
              {policies.map((p) => (
                <tr key={p.priority}>
                  <td className="mono">{p.priority}</td>
                  <td><input type="number" className="input" value={p.first_response_minutes} data-testid={`config-fr-minutes-${p.priority}`} onChange={(e) => updatePolicy(p.priority, "first_response_minutes", Number(e.target.value))} /></td>
                  <td><input type="number" className="input" value={p.resolve_minutes} data-testid={`config-resolve-minutes-${p.priority}`} onChange={(e) => updatePolicy(p.priority, "resolve_minutes", Number(e.target.value))} /></td>
                  <td><button className="btn btn-secondary btn-sm" data-testid={`config-save-policy-${p.priority}`} onClick={() => savePolicy(p)}>Save</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
