import React from "react";
import { Link } from "react-router-dom";

function FeatureCard({ title, description }) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
      <div className="text-base font-bold text-gray-900">{title}</div>
      <div className="mt-2 text-sm text-gray-700">{description}</div>
    </div>
  );
}

function PortalCard({ title, description, to, buttonLabel }) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6 flex flex-col">
      <div className="text-xl font-bold text-gray-900">{title}</div>
      <div className="mt-2 text-sm text-gray-700 flex-1">{description}</div>
      <div className="mt-5">
        <Link to={to} className="inline-block bg-[#FACC15] hover:bg-yellow-400 text-gray-900 font-semibold rounded-lg px-4 py-2">
          {buttonLabel}
        </Link>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="bg-white min-h-screen">
      <section className="py-10">
        <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
          <div className="text-3xl md:text-4xl font-extrabold tracking-tight text-gray-900">
            Smart Volunteer Allocation System
          </div>
          <div className="mt-3 text-gray-700 text-base md:text-lg">
            Powered by Enhanced SWAM AI Framework + Random Forest ML
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <PortalCard
          title="NGO Portal"
          description="Create community tasks, run AI-driven allocations, and manage assignments end-to-end."
          to="/ngo/login"
          buttonLabel="Go to NGO Login"
        />
        <PortalCard
          title="Student Portal"
          description="Build your profile, get matched to the best tasks, and track AICTE points earned."
          to="/student/login"
          buttonLabel="Go to Student Login"
        />
        <PortalCard
          title="Administrator"
          description="Manage all NGOs and student accounts, and use every NGO or student feature from one login."
          to="/admin/login"
          buttonLabel="Admin Login"
        />
      </section>

      <section className="mt-10">
        <div className="text-lg font-bold text-gray-900 mb-4">Key Features</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard title="ESWAM Matching" description="Multi-factor scoring combining skills, willingness, availability, urgency, fairness, and location proximity." />
          <FeatureCard title="Fairness-Aware" description="Balances workload by prioritizing volunteers with fewer completed tasks." />
          <FeatureCard title="Location Sensing" description="Uses proximity scoring based on normalized Haversine distance (up to 100km)." />
          <FeatureCard title="Urgency Priority" description="Urgent tasks are prioritized through normalized urgency handling in ESWAM." />
          <FeatureCard title="ML Prediction" description="Random Forest predicts assignment success probability using engineered features." />
          <FeatureCard title="AICTE Points" description="Computes earned points as a weighted sum of activity hours and point rates." />
        </div>
      </section>

      <section className="mt-10">
        <div className="bg-blue-50 border border-blue-100 rounded-xl shadow p-6">
          <div className="text-sm text-gray-700">
            New here?{" "}
            <Link className="text-blue-700 font-semibold hover:underline" to="/ngo/register">
              NGO Register
            </Link>{" "}
            or{" "}
            <Link className="text-blue-700 font-semibold hover:underline" to="/student/register">
              Student Register
            </Link>
            , or{" "}
            <Link className="text-blue-700 font-semibold hover:underline" to="/admin/register">
              Admin Register
            </Link>{" "}
            (requires server secret).
          </div>
        </div>
      </section>
    </div>
  );
}

