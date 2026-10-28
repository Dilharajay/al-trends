import React, { useState } from 'react';
import { Sliders, Zap, Loader2, TrendingUp } from 'lucide-react';
import { predictCutoff } from '../api';

export default function CutoffPredictor({ metadata }) {
  const initialUni = metadata.universities.includes('University of Colombo')
    ? 'University of Colombo'
    : (metadata.universities[0] || '');

  const [uni, setUni] = useState(initialUni);

  // Available courses dynamically filtered by selected university
  const availableCourses = (metadata.university_courses && metadata.university_courses[uni])
    ? metadata.university_courses[uni]
    : metadata.courses;

  const [course, setCourse] = useState(
    availableCourses.includes('MEDICINE') ? 'MEDICINE' : (availableCourses[0] || '')
  );

  const [district, setDistrict] = useState('COLOMBO');
  const [year, setYear] = useState(2026);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleUniChange = (newUni) => {
    setUni(newUni);
    const newCourses = (metadata.university_courses && metadata.university_courses[newUni])
      ? metadata.university_courses[newUni]
      : metadata.courses;

    if (!newCourses.includes(course)) {
      setCourse(newCourses[0] || '');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await predictCutoff({
        course_name: course,
        university_name: uni,
        district_name: district,
        exam_year: parseInt(year),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const hist = result?.historical_stats;
  const delta = (result && hist?.mean !== null && hist?.mean !== undefined)
    ? result.predicted_cutoff_z - hist.mean
    : null;

  const minScale = hist?.min ?? 1.5;
  const maxScale = hist?.max ?? 2.5;
  const span = Math.max(0.1, maxScale - minScale);
  const pct = result
    ? Math.min(100, Math.max(0, ((result.predicted_cutoff_z - minScale) / span) * 100))
    : 50;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Parameter Selection Form */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-2.5 mb-5 pb-3 border-b border-slate-100">
          <div className="p-2 rounded-lg bg-sky-50 text-sky-600">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Forecast Parameters</h2>
            <p className="text-xs text-slate-500">Configure university, course & candidate district</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 1. University Selection */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              University
            </label>
            <select
              value={uni}
              onChange={(e) => handleUniChange(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white shadow-sm"
            >
              {metadata.universities.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          </div>

          {/* 2. Target Course Selection (Filtered by selected university) */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                Target Course
              </label>
              <span className="text-[11px] font-semibold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-200">
                {availableCourses.length} programs offered
              </span>
            </div>
            <select
              value={course}
              onChange={(e) => setCourse(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white shadow-sm"
            >
              {availableCourses.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* 3. Candidate District */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Candidate District
            </label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white shadow-sm"
            >
              {metadata.districts.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          {/* 4. Exam Year */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Exam Year
            </label>
            <input
              type="number"
              min="2024"
              max="2030"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white shadow-sm"
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-medium text-sm shadow-md transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Forecasting...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>Predict Cutoff Z-Score</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results Display */}
      <div className="lg:col-span-2">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm min-h-[400px] flex flex-col justify-center">
          {!result ? (
            <div className="text-center py-16">
              <div className="w-14 h-14 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center mb-3">
                <TrendingUp className="w-7 h-7" />
              </div>
              <h3 className="text-base font-medium text-slate-700">No Forecast Generated Yet</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                Select a university on the left to see its offered degree programs, then click 'Predict Cutoff Z-Score'.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex flex-wrap justify-between items-start gap-4 pb-4 border-b border-slate-100">
                <div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-sky-50 text-sky-700 border border-sky-200">
                    {result.course_name}
                  </span>
                  <h3 className="text-xl font-bold text-slate-900 mt-2">{result.university_name}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    District: <strong className="text-slate-700">{result.district_name}</strong> | Exam Year: <strong className="text-slate-700">{result.exam_year}</strong>
                  </p>
                </div>
                <span className="px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wide bg-amber-100 text-amber-800 border border-amber-300">
                  {result.competitiveness_band || 'Competitive'}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <p className="text-xs font-medium text-slate-500">Predicted Cutoff Z</p>
                  <p className="text-2xl font-bold text-sky-600 mt-1">{result.predicted_cutoff_z.toFixed(4)}</p>
                  {delta !== null && (
                    <p className={`text-xs font-semibold mt-0.5 ${delta >= 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                      {delta >= 0 ? `+${delta.toFixed(4)}` : delta.toFixed(4)} vs mean
                    </p>
                  )}
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <p className="text-xs font-medium text-slate-500">Historical Mean</p>
                  <p className="text-2xl font-bold text-slate-800 mt-1">
                    {hist?.mean !== undefined && hist?.mean !== null ? hist.mean.toFixed(4) : 'N/A'}
                  </p>
                  {hist?.std !== undefined && hist?.std !== null && (
                    <p className="text-xs text-slate-500 mt-0.5">± {hist.std.toFixed(4)} SD</p>
                  )}
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <p className="text-xs font-medium text-slate-500">Historical Min</p>
                  <p className="text-2xl font-bold text-slate-800 mt-1">
                    {hist?.min !== undefined && hist?.min !== null ? hist.min.toFixed(4) : 'N/A'}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">Lowest recorded</p>
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                  <p className="text-xs font-medium text-slate-500">Historical Max</p>
                  <p className="text-2xl font-bold text-slate-800 mt-1">
                    {hist?.max !== undefined && hist?.max !== null ? hist.max.toFixed(4) : 'N/A'}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">Peak threshold</p>
                </div>
              </div>

              {/* Scale Benchmark */}
              {hist && hist.min !== null && (
                <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                  <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3">Z-Score Scale Benchmark</h4>
                  <div className="relative pt-6 pb-2">
                    <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden flex">
                      <div className="bg-emerald-300 w-1/3"></div>
                      <div className="bg-amber-300 w-1/3"></div>
                      <div className="bg-red-400 w-1/3"></div>
                    </div>
                    <div
                      className="absolute top-0 transform -translate-x-1/2 flex flex-col items-center"
                      style={{ left: `${pct}%` }}
                    >
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-700 text-white shadow-sm">
                        Pred: {result.predicted_cutoff_z.toFixed(2)}
                      </span>
                      <div className="w-0.5 h-6 bg-sky-700"></div>
                    </div>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 mt-2 font-mono">
                    <span>Min: {hist.min.toFixed(2)}</span>
                    <span>Mean: {hist.mean.toFixed(2)}</span>
                    <span>Max: {hist.max.toFixed(2)}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
