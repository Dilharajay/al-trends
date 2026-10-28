import React, { useState } from 'react';
import { UserCheck, Search, Loader2 } from 'lucide-react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { evaluateStudent } from '../api';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function StudentAnalyzer({ metadata }) {
  const [studentZ, setStudentZ] = useState(1.85);
  const [district, setDistrict] = useState('COLOMBO');
  const [courseFilter, setCourseFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await evaluateStudent({
        student_z_score: parseFloat(studentZ),
        district_name: district,
        course_name: courseFilter.trim() ? courseFilter.trim() : null,
        exam_year: 2026,
      });
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data for top 15 results
  const top15 = results?.evaluations?.slice(0, 15) || [];
  const chartData = {
    labels: top15.map((e) => `${e.course_name} (${e.university_name})`),
    datasets: [
      {
        label: 'Admission Margin (ΔZ)',
        data: top15.map((e) => e.margin),
        backgroundColor: top15.map((e) => {
          if (e.status === 'Safe') return '#16a34a';
          if (e.status === 'Possible') return '#0284c7';
          if (e.status === 'Competitive') return '#d97706';
          return '#dc2626';
        }),
        borderRadius: 6,
      },
    ],
  };

  const chartOptions = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        grid: { color: '#f1f5f9' },
        title: { display: true, text: 'Margin ΔZ (Positive = Safe margin over cutoff)' },
      },
      y: {
        ticks: { font: { size: 11 } },
      },
    },
  };

  return (
    <div className="space-y-6">
      {/* Parameter Input Form */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-2.5 mb-5 pb-3 border-b border-slate-100">
          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Student Profile & Admission Margins</h2>
            <p className="text-xs text-slate-500">Calculate eligibility margin (Student Z - Forecasted Cutoff)</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Your A/L Z-Score
            </label>
            <input
              type="number"
              step="0.0001"
              value={studentZ}
              onChange={(e) => setStudentZ(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Administrative District
            </label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
            >
              {metadata.districts.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Course Keyword Filter
            </label>
            <input
              type="text"
              placeholder="e.g. ENGINEERING, MEDICINE"
              value={courseFilter}
              onChange={(e) => setCourseFilter(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm shadow-md transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Evaluating...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Analyze Eligibility</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
            {error}
          </div>
        )}
      </div>

      {/* Results View */}
      {results && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Programs Evaluated</p>
              <p className="text-3xl font-bold text-slate-800 mt-2">{results.total_evaluated}</p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Eligible Programs</p>
              <p className="text-3xl font-bold text-emerald-600 mt-2">{results.eligible_count}</p>
              <p className="text-xs text-slate-400 mt-0.5">Safe + Possible chances</p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Top Safety Margin</p>
              <p className="text-3xl font-bold text-sky-600 mt-2">
                {results.evaluations.length > 0 && results.evaluations[0].margin >= 0 ? '+' : ''}
                {results.evaluations.length > 0 ? results.evaluations[0].margin.toFixed(4) : '0.0000'}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">Highest qualifying headroom</p>
            </div>
          </div>

          {/* Margin Chart */}
          {top15.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900 mb-4">
                Top 15 Programs Ranked by Admission Margin ({district} District)
              </h3>
              <div className="h-96 w-full relative">
                <Bar data={chartData} options={chartOptions} />
              </div>
            </div>
          )}

          {/* Table */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="text-base font-semibold text-slate-900">Program Options Breakdown</h3>
              <span className="text-xs text-slate-500">Sorted by highest admission margin</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-600 uppercase text-[11px] font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-6">Course Name</th>
                    <th className="py-3 px-6">University</th>
                    <th className="py-3 px-6 text-right">Forecast Cutoff Z</th>
                    <th className="py-3 px-6 text-right">Margin (ΔZ)</th>
                    <th className="py-3 px-6 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {results.evaluations.map((item, idx) => {
                    let badgeClass = 'text-rose-700 bg-rose-50 border-rose-200';
                    if (item.status === 'Safe') badgeClass = 'text-emerald-700 bg-emerald-50 border-emerald-200';
                    else if (item.status === 'Possible') badgeClass = 'text-sky-700 bg-sky-50 border-sky-200';
                    else if (item.status === 'Competitive') badgeClass = 'text-amber-700 bg-amber-50 border-amber-200';

                    return (
                      <tr key={idx} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-6 font-medium text-slate-900">{item.course_name}</td>
                        <td className="py-3 px-6 text-slate-600">{item.university_name}</td>
                        <td className="py-3 px-6 text-right font-mono font-semibold text-slate-800">
                          {item.predicted_cutoff_z.toFixed(4)}
                        </td>
                        <td className={`py-3 px-6 text-right font-mono font-semibold ${item.margin >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {item.margin >= 0 ? `+${item.margin.toFixed(4)}` : item.margin.toFixed(4)}
                        </td>
                        <td className="py-3 px-6 text-center">
                          <span className={`inline-block px-2.5 py-1 text-xs font-bold rounded-full border ${badgeClass}`}>
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
