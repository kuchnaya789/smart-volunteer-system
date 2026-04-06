import React, { useMemo, useState } from "react";

function clamp01(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function pct(x) {
  return Math.round(clamp01(x) * 100);
}

function ProgressRow({ label, value01, colorClass }) {
  const valuePct = pct(value01);
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <div className="font-semibold text-gray-900">{label}</div>
        <div className="font-semibold text-gray-700">{valuePct}%</div>
      </div>
      <div className="mt-2 h-3 w-full rounded-full bg-gray-200">
        <div className={`h-3 rounded-full ${colorClass}`} style={{ width: `${valuePct}%` }} />
      </div>
    </div>
  );
}

function ScoreNumber({ label, value, emphasize, colorClass }) {
  const n = typeof value === "number" ? value : Number(value);
  const display = Number.isFinite(n) ? n.toFixed(4) : "—";
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
      <div className="text-sm font-semibold text-gray-700">{label}</div>
      <div className={`${emphasize ? "text-3xl" : "text-2xl"} font-extrabold ${colorClass || "text-gray-900"} mt-2`}>
        {display}
      </div>
    </div>
  );
}

function finalColor(finalScore) {
  const s = clamp01(finalScore);
  if (s < 0.4) return "text-red-600";
  if (s < 0.7) return "text-yellow-600";
  return "text-green-600";
}

export default function ScoreBreakdown({ scoreBreakdown, allCandidates }) {
  const [showCandidates, setShowCandidates] = useState(false);

  const breakdown = scoreBreakdown || {};
  const candidates = Array.isArray(allCandidates) ? allCandidates : [];

  const rows = useMemo(
    () => [
      { label: "Skill Match", value: breakdown.skill_match, color: "bg-blue-600" },
      { label: "Willingness", value: breakdown.willingness, color: "bg-blue-600" },
      { label: "Availability", value: breakdown.availability, color: "bg-blue-600" },
      { label: "Urgency", value: breakdown.urgency_handled, color: "bg-orange-500" },
      { label: "Fairness", value: breakdown.fairness, color: "bg-green-600" },
      { label: "Location Proximity", value: breakdown.location_proximity, color: "bg-purple-600" },
    ],
    [breakdown]
  );

  const aicteRows = useMemo(
    () => [
      { label: "Volunteer Experience", value: breakdown.volunteer_experience_norm ?? breakdown.volunteer_aicte_norm, color: "bg-indigo-600" },
      { label: "Task Opportunity", value: breakdown.task_opportunity_norm ?? breakdown.task_points_norm, color: "bg-pink-600" },
      { label: "Reliability Score", value: breakdown.reliability_score, color: "bg-emerald-600" },
    ],
    [breakdown]
  );

  const formula = breakdown.formula || "Final Score = 0.6 × ESWAM + 0.25 × ML_Probability + 0.15 × AICTE_Factor";

  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-lg font-extrabold text-gray-900">AI Score Breakdown</div>
          <div className="mt-1 text-sm text-gray-700">{formula}</div>
        </div>
        {candidates.length > 0 && (
          <button
            className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2 text-sm font-semibold"
            onClick={() => setShowCandidates((v) => !v)}
            type="button"
          >
            {showCandidates ? "Hide Candidates" : "Show Candidates"}
          </button>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          {rows.map((r) => (
            <ProgressRow key={r.label} label={r.label} value01={r.value} colorClass={r.color} />
          ))}
          <div className="pt-3 border-t border-blue-100">
            <div className="text-sm font-extrabold text-gray-900 mb-3">AICTE Contribution</div>
            <div className="space-y-4">
              {aicteRows.map((r) => (
                <ProgressRow key={r.label} label={r.label} value01={r.value} colorClass={r.color} />
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          <ScoreNumber label="ESWAM Score" value={breakdown.eswam_score} />
          <ScoreNumber label="ML Success Probability" value={breakdown.ml_success_probability} />
          <ScoreNumber label="AICTE Factor" value={breakdown.aicte_factor} />
          <ScoreNumber
            label="Final Score"
            value={breakdown.final_score}
            emphasize
            colorClass={finalColor(breakdown.final_score)}
          />
        </div>
      </div>

      {showCandidates && candidates.length > 0 && (
        <div className="mt-6">
          <div className="text-sm font-bold text-gray-900 mb-3">All Candidates (Ranked)</div>
          <div className="overflow-x-auto rounded-lg border border-blue-100 bg-white">
            <table className="min-w-full text-sm">
              <thead className="bg-[#1E3A8A] text-white">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Rank</th>
                  <th className="px-4 py-3 text-left font-semibold">Volunteer</th>
                  <th className="px-4 py-3 text-left font-semibold">Final</th>
                  <th className="px-4 py-3 text-left font-semibold">ESWAM</th>
                  <th className="px-4 py-3 text-left font-semibold">ML Prob</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c, idx) => {
                  const name = c?.name || c?.full_name || c?.email || c?.volunteer_name || "Volunteer";
                  const finalScore = c?.final_score ?? c?.finalScore ?? c?.score ?? 0;
                  const eswam = c?.eswam_score ?? c?.eswamScore ?? c?.eswam ?? 0;
                  const ml = c?.ml_success_probability ?? c?.mlProbability ?? c?.ml ?? 0;
                  return (
                    <tr key={c?._id || c?.volunteer_id || idx} className={idx % 2 ? "bg-blue-50/40" : "bg-white"}>
                      <td className="px-4 py-3 font-semibold text-gray-900">{idx + 1}</td>
                      <td className="px-4 py-3 text-gray-900">{name}</td>
                      <td className={`px-4 py-3 font-extrabold ${finalColor(finalScore)}`}>
                        {Number(finalScore).toFixed(4)}
                      </td>
                      <td className="px-4 py-3 text-gray-900">{Number(eswam).toFixed(4)}</td>
                      <td className="px-4 py-3 text-gray-900">{Number(ml).toFixed(4)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

