import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Star } from "lucide-react";
import { csatApi } from "@/api/endpoints";
import { formatApiError } from "@/api/client";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { CsatSurvey } from "@/types";
import "@/pages/tickets/Tickets.css";

export default function CsatPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [survey, setSurvey] = useState<CsatSurvey | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id) return;
    csatApi.get(id).then(({ data }) => setSurvey(data)).catch((err) => setError(formatApiError(err?.response?.data?.detail))).finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async () => {
    if (!id || rating === 0) return;
    setSubmitting(true);
    setError("");
    try {
      const { data } = await csatApi.submit(id, rating, comment);
      setSurvey(data);
    } catch (err: any) {
      setError(formatApiError(err?.response?.data?.detail) || "Could not submit rating.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner fullPage />;

  return (
    <div className="page csat-page" data-testid="csat-page">
      <div className="card csat-card">
        <h1>Rate your support experience</h1>
        {survey?.technician_username && <p className="text-muted">Technician: {survey.technician_username}</p>}

        {error && <div className="form-error" data-testid="csat-error-message">{error}</div>}

        {survey?.status === "submitted" ? (
          <div className="csat-submitted" data-testid="csat-submitted-state">
            <p>Thanks for your feedback! You rated this ticket {survey.rating} / 5.</p>
            {survey.comment && <p className="text-muted">&quot;{survey.comment}&quot;</p>}
            <button className="btn btn-secondary" data-testid="csat-back-to-ticket-button" onClick={() => navigate(`/tickets/${id}`)}>Back to ticket</button>
          </div>
        ) : (
          <>
            <div className="csat-stars" data-testid="csat-star-rating">
              {[1, 2, 3, 4, 5].map((n) => (
                <button key={n} type="button" data-testid={`csat-star-${n}`} onClick={() => setRating(n)} className={n <= rating ? "csat-star-active" : ""}>
                  <Star size={32} fill={n <= rating ? "currentColor" : "none"} />
                </button>
              ))}
            </div>
            <textarea className="textarea" placeholder="Any additional comments? (optional)" value={comment} data-testid="csat-comment-input" onChange={(e) => setComment(e.target.value)} />
            <button className="btn btn-primary" data-testid="csat-submit-button" disabled={rating === 0 || submitting} onClick={handleSubmit}>
              {submitting ? "Submitting..." : "Submit rating"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
