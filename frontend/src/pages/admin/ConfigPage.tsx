import React, { useEffect, useState } from "react";
import { assignmentApi, calendarApi, ticketsApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { BusinessCalendar } from "@/types";
import "@/pages/admin/Admin.css";

interface SlaPolicy { priority: string; first_response_minutes: number; resolve_minutes: number; }
interface PriorityRow { impact: string; urgency: string; priority: string; }

const LEVELS = ["high", "medium", "low"];
const PRIORITIES = ["P1", "P2", "P3", "P4"];
const DAYS = [
  { value: 0, label: "Mon" }, { value: 1, label: "Tue" }, { value: 2, label: "Wed" },
  { value: 3, label: "Thu" }, { value: 4, label: "Fri" }, { value: 5, label: "Sat" }, { value: 6, label: "Sun" },
];

export default function ConfigPage() {
  const [algorithms, setAlgorithms] = useState<string[]>([]);
  const [active, setActive] = useState("");
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [matrix, setMatrix] = useState<PriorityRow[]>([]);
  const [calendar, setCalendar] = useState<BusinessCalendar | null>(null);
  const [holidayInput, setHolidayInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      assignmentApi.getConfig().then(({ data }) => { setAlgorithms(data.available_algorithms); setActive(data.active_algorithm); }),
      ticketsApi.slaPolicies().then(({ data }) => setPolicies(data)),
      ticketsApi.priorityMatrix().then(({ data }) => setMatrix(data)),
      calendarApi.get().then(({ data }) => setCalendar(data)),
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

  const priorityFor = (impact: string, urgency: string) =>
    matrix.find((m) => m.impact === impact && m.urgency === urgency)?.priority || "P3";

  const handleMatrixChange = async (impact: string, urgency: string, priority: string) => {
    setError("");
    setMessage("");
    try {
      await ticketsApi.updatePriorityMatrix(impact, urgency, priority);
      setMatrix((rows) => rows.map((r) => (r.impact === impact && r.urgency === urgency ? { ...r, priority } : r)));
      setMessage(`Priority matrix updated: ${impact} impact / ${urgency} urgency -> ${priority}.`);
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not update priority matrix.");
    }
  };

  const toggleBusinessDay = (day: number) => {
    if (!calendar) return;
    const days = calendar.business_days.includes(day)
      ? calendar.business_days.filter((d) => d !== day)
      : [...calendar.business_days, day].sort((a, b) => a - b);
    setCalendar({ ...calendar, business_days: days });
  };

  const saveCalendar = async () => {
    if (!calendar) return;
    setError("");
    setMessage("");
    try {
      const { data } = await calendarApi.update(calendar);
      setCalendar(data);
      setMessage("Business calendar saved.");
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not save business calendar.");
    }
  };

  const addHoliday = () => {
    if (!calendar || !holidayInput || calendar.holidays.includes(holidayInput)) return;
    setCalendar({ ...calendar, holidays: [...calendar.holidays, holidayInput].sort() });
    setHolidayInput("");
  };

  const removeHoliday = (date: string) => {
    if (!calendar) return;
    setCalendar({ ...calendar, holidays: calendar.holidays.filter((d) => d !== date) });
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

      <div className="card config-section">
        <h3>Impact &times; Urgency priority matrix</h3>
        <p className="text-muted">Change the resulting priority for any impact/urgency combination.</p>
        <div className="table-wrapper">
          <table className="data-table priority-matrix-table">
            <thead>
              <tr>
                <th>Impact \ Urgency</th>
                {LEVELS.map((u) => <th key={u} className="mono">{u}</th>)}
              </tr>
            </thead>
            <tbody>
              {LEVELS.map((impact) => (
                <tr key={impact}>
                  <td className="mono">{impact}</td>
                  {LEVELS.map((urgency) => (
                    <td key={urgency}>
                      <select
                        className="select"
                        value={priorityFor(impact, urgency)}
                        data-testid={`config-matrix-${impact}-${urgency}`}
                        onChange={(e) => handleMatrixChange(impact, urgency, e.target.value)}
                      >
                        {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                      </select>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {calendar && (
        <div className="card config-section">
          <h3>Business calendar</h3>
          <p className="text-muted">Global working days/hours used to calculate SLA due dates in business time.</p>
          <div className="business-calendar-days">
            {DAYS.map((d) => (
              <label key={d.value} className={`business-calendar-day ${calendar.business_days.includes(d.value) ? "business-calendar-day-active" : ""}`}>
                <input
                  type="checkbox"
                  data-testid={`config-calendar-day-${d.value}`}
                  checked={calendar.business_days.includes(d.value)}
                  onChange={() => toggleBusinessDay(d.value)}
                />
                {d.label}
              </label>
            ))}
          </div>
          <div className="business-calendar-hours">
            <div className="field">
              <label className="label">Start time</label>
              <input
                type="time"
                className="input"
                data-testid="config-calendar-start-time"
                value={`${String(calendar.start_hour).padStart(2, "0")}:${String(calendar.start_minute).padStart(2, "0")}`}
                onChange={(e) => {
                  const [h, m] = e.target.value.split(":").map(Number);
                  setCalendar({ ...calendar, start_hour: h, start_minute: m });
                }}
              />
            </div>
            <div className="field">
              <label className="label">End time</label>
              <input
                type="time"
                className="input"
                data-testid="config-calendar-end-time"
                value={`${String(calendar.end_hour).padStart(2, "0")}:${String(calendar.end_minute).padStart(2, "0")}`}
                onChange={(e) => {
                  const [h, m] = e.target.value.split(":").map(Number);
                  setCalendar({ ...calendar, end_hour: h, end_minute: m });
                }}
              />
            </div>
          </div>
          <div className="field">
            <label className="label">Holidays</label>
            <div className="business-calendar-holiday-add">
              <input type="date" className="input" data-testid="config-calendar-holiday-input" value={holidayInput} onChange={(e) => setHolidayInput(e.target.value)} />
              <button type="button" className="btn btn-secondary btn-sm" data-testid="config-calendar-add-holiday-button" onClick={addHoliday}>Add holiday</button>
            </div>
            <div className="business-calendar-holidays">
              {calendar.holidays.length === 0 && <span className="text-muted">No holidays configured.</span>}
              {calendar.holidays.map((h) => (
                <span key={h} className="tag-chip business-calendar-holiday-chip" data-testid={`config-calendar-holiday-${h}`}>
                  {h}
                  <button type="button" data-testid={`config-calendar-remove-holiday-${h}`} onClick={() => removeHoliday(h)}>&times;</button>
                </span>
              ))}
            </div>
          </div>
          <button className="btn btn-primary btn-sm" data-testid="config-calendar-save-button" onClick={saveCalendar}>Save business calendar</button>
        </div>
      )}
    </div>
  );
}
