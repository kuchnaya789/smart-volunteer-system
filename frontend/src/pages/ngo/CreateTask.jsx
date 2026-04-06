import React, { useEffect, useMemo, useState } from "react";
import api from "../../api/axios.js";
import ScoreBreakdown from "../../components/ScoreBreakdown.jsx";

function UrgencyMeta({ value }) {
  const v = Number(value);
  const label = v <= 3 ? "Low" : v <= 5 ? "Medium" : v <= 8 ? "High" : "Critical";
  const color = v <= 3 ? "text-green-700" : v <= 5 ? "text-yellow-700" : v <= 8 ? "text-orange-700" : "text-red-700";
  return (
    <div className={`text-sm font-semibold ${color}`}>
      {v} / 10 ({label})
    </div>
  );
}

const ACTIVITY_TYPES = [
  "community_service",
  "teaching",
  "health_camp",
  "disaster_relief",
  "environment",
  "skill_training",
  "event_management",
];

export default function CreateTask() {
  const authRole = typeof window !== "undefined" ? localStorage.getItem("role") || "" : "";
  const isAdmin = authRole === "admin";

  const [ngoList, setNgoList] = useState([]);
  const [selectedNgoId, setSelectedNgoId] = useState("");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [skillInput, setSkillInput] = useState("");
  const [requiredSkills, setRequiredSkills] = useState([]);

  const [urgency, setUrgency] = useState(6);
  const [location, setLocation] = useState("");
  const [locationLat, setLocationLat] = useState(null);
  const [locationLng, setLocationLng] = useState(null);
  const [hoursRequired, setHoursRequired] = useState(10);
  const [pointsPerHour, setPointsPerHour] = useState(2.0);
  const [activityType, setActivityType] = useState("community_service");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [createdTaskId, setCreatedTaskId] = useState("");

  const [assignLoading, setAssignLoading] = useState(false);
  const [assignmentResult, setAssignmentResult] = useState(null);

  const normalizedSkills = useMemo(
    () => requiredSkills.map((s) => s.trim()).filter(Boolean),
    [requiredSkills]
  );

  useEffect(() => {
    if (!isAdmin) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get("/admin/users", { params: { role: "ngo" } });
        const rows = Array.isArray(res.data) ? res.data : [];
        if (!cancelled) {
          setNgoList(rows);
          setSelectedNgoId((prev) => prev || (rows[0]?._id || ""));
        }
      } catch {
        if (!cancelled) setNgoList([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isAdmin]);

  const addSkill = (raw) => {
    const s = (raw || "").trim();
    if (!s) return;
    setRequiredSkills((prev) => {
      const exists = prev.some((x) => x.toLowerCase() === s.toLowerCase());
      return exists ? prev : [...prev, s];
    });
  };

  const removeSkill = (s) => setRequiredSkills((prev) => prev.filter((x) => x !== s));

  const onSkillKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addSkill(skillInput);
      setSkillInput("");
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setAssignmentResult(null);
    setCreatedTaskId("");
    setLoading(true);
    try {
      const trimmedSkill = skillInput.trim();
      let skillsPayload = normalizedSkills;
      if (trimmedSkill) {
        const dup = normalizedSkills.some((x) => x.toLowerCase() === trimmedSkill.toLowerCase());
        skillsPayload = dup ? normalizedSkills : [...normalizedSkills, trimmedSkill];
      }
      if (skillsPayload.length === 0) {
        setError("Add at least one required skill.");
        setLoading(false);
        return;
      }
      if (locationLat === null || locationLng === null || !Number.isFinite(locationLat) || !Number.isFinite(locationLng)) {
        setError("Enter numeric latitude and longitude.");
        setLoading(false);
        return;
      }
      const body = {
        title,
        description,
        required_skills: skillsPayload,
        urgency,
        location,
        location_lat: locationLat,
        location_lng: locationLng,
        hours_required: Number(hoursRequired),
        points_per_hour: Number(pointsPerHour),
        activity_type: activityType,
      };
      if (isAdmin) {
        if (!selectedNgoId) {
          setError("Select which NGO owns this task.");
          setLoading(false);
          return;
        }
        body.ngo_id = selectedNgoId;
      }
      const res = await api.post("/tasks", body);

      const taskId = res.data?._id || res.data?.task_id || res.data?.taskId || "";
      setCreatedTaskId(taskId);
      setRequiredSkills(skillsPayload);
      setSkillInput("");
      setSuccess("Task created successfully.");
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to create task.");
    } finally {
      setLoading(false);
    }
  };

  const runAssignment = async () => {
    if (!createdTaskId) return;
    setAssignLoading(true);
    setError("");
    try {
      const res = await api.post(`/assignments/run/${createdTaskId}`);
      setAssignmentResult(res.data || null);
      setSuccess("AI assignment completed successfully.");
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "AI assignment failed.");
    } finally {
      setAssignLoading(false);
    }
  };

  return (
    <div className="bg-white min-h-screen">
      <div className="text-2xl font-extrabold text-gray-900">Create Task</div>
      <div className="mt-1 text-sm text-gray-700">Provide task details and required skills. Then run the AI allocation pipeline.</div>

      {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {success && <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">{success}</div>}

      <form onSubmit={onSubmit} className="mt-6 bg-blue-50 border border-blue-100 rounded-xl shadow p-6 space-y-5">
        {isAdmin && (
          <div>
            <label className="text-sm font-semibold text-gray-900">NGO owner</label>
            <select
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
              value={selectedNgoId}
              onChange={(e) => setSelectedNgoId(e.target.value)}
              required
            >
              <option value="" disabled>
                Select NGO…
              </option>
              {ngoList.map((n) => (
                <option key={n._id} value={n._id}>
                  {n.name || n.email || n._id}
                </option>
              ))}
            </select>
            {ngoList.length === 0 && (
              <p className="mt-2 text-xs text-amber-800">Register at least one NGO before creating tasks.</p>
            )}
          </div>
        )}

        <div>
          <label className="text-sm font-semibold text-gray-900">Task Title</label>
          <input
            className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="e.g., Community Health Awareness Drive"
          />
        </div>

        <div>
          <label className="text-sm font-semibold text-gray-900">Description</label>
          <textarea
            className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            required
            placeholder="Describe what volunteers will do and any constraints."
          />
        </div>

        <div>
          <label className="text-sm font-semibold text-gray-900">Required Skills</label>
          <input
            className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
            value={skillInput}
            onChange={(e) => setSkillInput(e.target.value)}
            onKeyDown={onSkillKeyDown}
            placeholder="Type a skill and press Enter (e.g., first-aid)"
          />
          {normalizedSkills.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {normalizedSkills.map((s) => (
                <span key={s} className="inline-flex items-center rounded-full bg-white px-3 py-1 text-xs font-semibold text-gray-900 ring-1 ring-gray-200">
                  {s}
                  <button
                    type="button"
                    onClick={() => removeSkill(s)}
                    className="ml-2 text-gray-500 hover:text-gray-900"
                    aria-label={`Remove ${s}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between gap-4">
            <label className="text-sm font-semibold text-gray-900">Urgency</label>
            <UrgencyMeta value={urgency} />
          </div>
          <input
            type="range"
            min="1"
            max="10"
            value={urgency}
            onChange={(e) => setUrgency(Number(e.target.value))}
            className="mt-2 w-full"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <label className="text-sm font-semibold text-gray-900">Location Name</label>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              required
              placeholder="e.g., Pune"
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-900">Latitude</label>
            <input
              type="number"
              step="any"
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={locationLat === null || locationLat === undefined ? "" : locationLat}
              onChange={(e) => {
                const raw = e.target.value;
                if (raw === "" || raw === "-") {
                  setLocationLat(null);
                  return;
                }
                const n = Number(raw);
                setLocationLat(Number.isFinite(n) ? n : null);
              }}
              required
              placeholder="18.5204"
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-900">Longitude</label>
            <input
              type="number"
              step="any"
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={locationLng === null || locationLng === undefined ? "" : locationLng}
              onChange={(e) => {
                const raw = e.target.value;
                if (raw === "" || raw === "-") {
                  setLocationLng(null);
                  return;
                }
                const n = Number(raw);
                setLocationLng(Number.isFinite(n) ? n : null);
              }}
              required
              placeholder="73.8567"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-semibold text-gray-900">Hours Required</label>
            <input
              type="number"
              min="1"
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={hoursRequired}
              onChange={(e) => setHoursRequired(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-900">Points Per Hour</label>
            <input
              type="number"
              step="0.1"
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={pointsPerHour}
              onChange={(e) => setPointsPerHour(e.target.value)}
              required
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-sm font-semibold text-gray-900">Activity Type</label>
            <select
              className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
              value={activityType}
              onChange={(e) => setActivityType(e.target.value)}
              required
            >
              {ACTIVITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            disabled={loading}
            className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2 disabled:opacity-60"
            type="submit"
          >
            {loading ? "Creating..." : "Create Task"}
          </button>

          {createdTaskId && (
            <button
              disabled={assignLoading}
              onClick={runAssignment}
              className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2 disabled:opacity-60"
              type="button"
            >
              {assignLoading ? "Running..." : "Run AI Assignment Now"}
            </button>
          )}
        </div>
      </form>

      {assignmentResult && (
        <div className="mt-8 space-y-6">
          <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
            <div className="text-lg font-extrabold text-gray-900">Assignment Result</div>
            <div className="mt-2 text-sm text-gray-700">
              Assigned Volunteer:{" "}
              <span className="font-semibold text-gray-900">
                {assignmentResult?.assigned_volunteer?.name ||
                  assignmentResult?.assigned_volunteer?.full_name ||
                  assignmentResult?.assigned_volunteer?.email ||
                  "—"}
              </span>
            </div>
          </div>

          <ScoreBreakdown
            scoreBreakdown={assignmentResult?.score_breakdown || assignmentResult?.scoreBreakdown}
            allCandidates={assignmentResult?.all_scores || assignmentResult?.allCandidates}
          />
        </div>
      )}
    </div>
  );
}

