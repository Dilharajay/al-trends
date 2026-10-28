import React, { useState } from 'react';
import { BarChart2, Layers, Loader2 } from 'lucide-react';
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
import { predictBatch } from '../api';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function UniversityComparison({ metadata }) {
  const [course, setCourse] = useState('ENGINEERING');
  const [district, setDistrict] = useState('KANDY');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Filter universities to only those offering this degree program
  const offeringUniversities = (metadata.course_universities && metadata.course_universities[course])
    ? metadata.course_universities[course]
    : metadata.universities;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const items = offeringUniversities.map((u) => ({
        course_name: course,
        university_name: u,
        district_name: district,
        exam_year: 2026,
      }));

      const data = await predictBatch(items);
      const sorted = [...data.predictions].sort(
        (a, b) => b.predicted_cutoff_z - a.predicted_cutoff_z
      );
      setResults(sorted);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = {
    labels: results?.map((p) => p.university_name) || [],
    datasets: [
      {
        label: 'Forecast Cutoff Z-Score',
        data: results?.map((p) => p.predicted_cutoff_z) || [],
        backgroundColor: '#0284c7',
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
        title: { display: true, text: 'Cutoff Z-Score' },
      },
      y: {
        ticks: { font: { size: 11 } },
      },
    },
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-2.5 mb-5 pb-3 border-b border-slate-100">
          <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
            <BarChart2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Multi-University Cutoff Comparison</h2>
            <p className="text-xs text-slate-500">Benchmark minimum cutoffs across state universities offering this program</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                Degree Program
              </label>
              <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-200">
                {offeringUniversities.length} offering universities
              </span>
            </div>
            <select
              value={course}
              onChange={(e) => setCourse(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white shadow-sm"
            >
              {metadata.courses.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Candidate District
            </label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white shadow-sm"
            >
              {metadata.districts.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-md transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Batch...</span>
              </>
            ) : (
              <>
                <Layers className="w-4 h-4" />
                <span>Run Batch Comparison</span>
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

      {results && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900 mb-4">
              Forecast Cutoffs by University: {course} ({district} District)
            </h3>
            <div className="h-96 w-full relative">
              <Bar data={chartData} options={chartOptions} />
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="text-base font-semibold text-slate-900">Comparative Cutoffs Breakdown</h3>
              <span className="text-xs text-slate-500">{results.length} universities offering {course}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-600 uppercase text-[11px] font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-6">University</th>
                    <th className="py-3 px-6 text-right">Predicted Cutoff Z</th>
                    <th className="py-3 px-6 text-right">Historical Mean</th>
                    <th className="py-3 px-6 text-center">Competitiveness</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {results.map((p, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-6 font-medium text-slate-900">{p.university_name}</td>
                      <td className="py-3 px-6 text-right font-mono font-semibold text-sky-600">
                        {p.predicted_cutoff_z.toFixed(4)}
                      </td>
                      <td className="py-3 px-6 text-right font-mono text-slate-600">
                        {p.historical_stats?.mean !== null && p.historical_stats?.mean !== undefined
                          ? p.historical_stats.mean.toFixed(4)
                          : 'N/A'}
                      </td>
                      <td className="py-3 px-6 text-center">
                        <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {p.competitiveness_band || 'Competitive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
