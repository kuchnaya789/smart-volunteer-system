import React, { useEffect, useMemo, useState } from "react";
import api from "../../api/axios.js";

function Toast({ message, onClose }) {
  if (!message) return null;
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800 shadow">
        <div className="flex items-start justify-between gap-4">
          <div className="font-semibold">{message}</div>
          <button onClick={onClose} className="text-green-900 font-bold" type="button" aria-label="Close">
            ×
          </button>
        </div>
      </div>
    </div>
  );
}

function WillingnessMeta({ value }) {
  const v = Number(value);
  const label = v <= 3 ? "Low" : v <= 7 ? "Moderate" : "High";
  const color = v <= 3 ? "text-red-700" : v <= 7 ? "text-yellow-700" : "text-green-700";
  return (
    <div className={`text-sm font-semibold ${color}`}>
      {v} / 10 ({label})
    </div>
  );
}

export default function StudentProfile() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState("");
  const [willingness, setWillingness] = useState(7);
  const [availabilityHours, setAvailabilityHours] = useState(10);
  const [location, setLocation] = useState("");
  const [locationLat, setLocationLat] = useState(null);
  const [locationLng, setLocationLng] = useState(null);

  const normalizedSkills = useMemo(() => skills.map((s) => s.trim()).filter(Boolean), [skills]);

  const addSkill = (raw) => {
    const s = (raw || "").trim();
    if (!s) return;
    setSkills((prev) => {
      const exists = prev.some((x) => x.toLowerCase() === s.toLowerCase());
      return exists ? prev : [...prev, s];
    });
  };
  const removeSkill = (s) => setSkills((prev) => prev.filter((x) => x !== s));
  const onSkillKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addSkill(skillInput);
      setSkillInput("");
    }
  };

  const loadProfile = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/assignments/my-assignments");
      const user = res.data?.user || res.data?.profile || res.data?.student || null;
      if (user) {
        setSkills(Array.isArray(user.skills) ? user.skills : []);
        setWillingness(Math.max(1, Math.min(10, Math.round((Number(user.willingness) || 0) * 10) || 7)));
        setAvailabilityHours(Math.max(1, Math.min(40, Math.round((Number(user.availability) || 0) * 40) || 10)));
        setLocation(user.location || "");
        const toNum = (v) => {
          if (v === null || v === undefined || v === "") return null;
          const n = typeof v === "number" ? v : Number(v);
          return Number.isFinite(n) ? n : null;
        };
        setLocationLat(toNum(user.location_lat));
        setLocationLng(toNum(user.location_lng));
      }
    } catch (err) {
      // Profile GET isn't specified in backend; this keeps UI functional even if only PUT exists.
      setError("");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const onSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    const trimmedPending = (skillInput || "").trim();
    let skillsToSave = normalizedSkills;
    if (trimmedPending) {
      const dup = normalizedSkills.some((x) => x.toLowerCase() === trimmedPending.toLowerCase());
      skillsToSave = dup ? normalizedSkills : [...normalizedSkills, trimmedPending];
    }
    try {
      if (locationLat === null || locationLng === null || !Number.isFinite(locationLat) || !Number.isFinite(locationLng)) {
        setError("Enter numeric latitude and longitude.");
        setSaving(false);
        return;
      }
      const res = await api.put("/auth/profile", {
        skills: skillsToSave,
        willingness,
        availability: availabilityHours,
        location,
        location_lat: locationLat,
        location_lng: locationLng,
      });
      const saved = res.data?.user;
      if (saved && Array.isArray(saved.skills)) {
        setSkills(saved.skills);
      } else {
        setSkills(skillsToSave);
      }
      setSkillInput("");
      setToast("Profile saved successfully.");
      window.setTimeout(() => setToast(""), 2500);
    } catch (err) {
      setError(err?.response?.data?.error || err?.response?.data?.message || "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white min-h-screen">
      <Toast message={toast} onClose={() => setToast("")} />

      <div className="text-2xl font-extrabold text-gray-900">Student Profile</div>
      <div className="mt-1 text-sm text-gray-700">Update your skills, willingness, availability, and location for better matching.</div>

      {error && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <form onSubmit={onSave} className="mt-6 bg-blue-50 border border-blue-100 rounded-xl shadow p-6 space-y-5">
        {loading ? (
          <div className="text-sm text-gray-700">Loading profile...</div>
        ) : (
          <>
            <div>
              <label className="text-sm font-semibold text-gray-900">Skills</label>
              <input
                className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 mt-1"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={onSkillKeyDown}
                placeholder="Type a skill and press Enter (e.g., teaching)"
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
                <label className="text-sm font-semibold text-gray-900">Willingness</label>
                <WillingnessMeta value={willingness} />
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={willingness}
                onChange={(e) => setWillingness(Number(e.target.value))}
                className="mt-2 w-full"
              />
            </div>

            <div>
              <div className="flex items-center justify-between gap-4">
                <label className="text-sm font-semibold text-gray-900">Availability (hours/week)</label>
                <div className="text-sm font-semibold text-gray-700">{availabilityHours} / 40</div>
              </div>
              <input
                type="range"
                min="1"
                max="40"
                value={availabilityHours}
                onChange={(e) => setAvailabilityHours(Number(e.target.value))}
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
                  placeholder="e.g., Mumbai"
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
                  placeholder="19.0760"
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
                  placeholder="72.8777"
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                disabled={saving}
                className="bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2 disabled:opacity-60"
                type="submit"
              >
                {saving ? "Saving..." : "Save Profile"}
              </button>
              <button
                onClick={loadProfile}
                className="bg-[#1E3A8A] hover:bg-blue-800 text-white rounded-lg px-4 py-2 disabled:opacity-60"
                type="button"
                disabled={saving}
              >
                Reload
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
}

