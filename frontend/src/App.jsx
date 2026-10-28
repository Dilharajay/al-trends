import React, { useState, useEffect } from 'react';
import { GraduationCap, Sparkles, UserCheck, BarChart2, Loader2 } from 'lucide-react';
import { fetchMetadata } from './api';
import CutoffPredictor from './components/CutoffPredictor';
import StudentAnalyzer from './components/StudentAnalyzer';
import UniversityComparison from './components/UniversityComparison';

export default function App() {
  const [activeTab, setActiveTab] = useState('predict');
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function init() {
      try {
        const data = await fetchMetadata();
        setMetadata(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-sky-600" />
        <p className="text-sm font-medium text-slate-600">Initializing Admission Intelligence Portal...</p>
      </div>
    );
  }

  if (error || !metadata) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white p-6 rounded-2xl border border-red-200 shadow-sm text-center">
          <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-3">
            <GraduationCap className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Service Connection Error</h3>
          <p className="text-xs text-slate-500 mb-4">{error || 'Failed to load system metadata.'}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-sky-600 text-white rounded-xl text-xs font-medium hover:bg-sky-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-sky-600 flex items-center justify-center text-white shadow-md">
                <GraduationCap className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900 leading-tight">Sri Lanka A/L Cutoffs AI</h1>
                <p className="text-xs text-slate-500 font-medium">University Admission & Z-Score Forecaster</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-2 sm:space-x-4 overflow-x-auto border-t border-slate-100 py-2 no-scrollbar">
            <button
              onClick={() => setActiveTab('predict')}
              className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-xl transition-all whitespace-nowrap ${
                activeTab === 'predict'
                  ? 'bg-sky-50 text-sky-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Cutoff Predictor
            </button>

            <button
              onClick={() => setActiveTab('student')}
              className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-xl transition-all whitespace-nowrap ${
                activeTab === 'student'
                  ? 'bg-emerald-50 text-emerald-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <UserCheck className="w-4 h-4 mr-2" />
              Student Admission Analyzer
            </button>

            <button
              onClick={() => setActiveTab('compare')}
              className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-xl transition-all whitespace-nowrap ${
                activeTab === 'compare'
                  ? 'bg-indigo-50 text-indigo-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <BarChart2 className="w-4 h-4 mr-2" />
              University Comparison
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'predict' && <CutoffPredictor metadata={metadata} />}
        {activeTab === 'student' && <StudentAnalyzer metadata={metadata} />}
        {activeTab === 'compare' && <UniversityComparison metadata={metadata} />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
          Sri Lanka G.C.E. A/L University Admissions Forecaster &bull; Powered by Machine Learning &amp; Official UGC Data
        </div>
      </footer>
    </div>
  );
}
