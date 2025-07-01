import React from 'react';
import { formatDistanceToNow } from 'date-fns';

const AnalysisResults = ({ results, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4">Analysis Results</h2>
        <div className="text-center py-4 text-gray-500">Loading...</div>
      </div>
    );
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-4">Analysis Results</h2>
      <div className="space-y-4">
        {results.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            No analysis results yet
          </div>
        ) : (
          results.map((result) => (
            <div
              key={result.id}
              className={`border rounded-lg p-4 ${
                result.alert_triggered ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-semibold">{result.analysis_type}</h3>
                  <p className="text-sm text-gray-600">{result.camera_name}</p>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${getConfidenceColor(result.confidence)}`}>
                    {(result.confidence * 100).toFixed(0)}% confident
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(result.created_at), { addSuffix: true })}
                  </p>
                </div>
              </div>
              
              <div className="bg-gray-100 rounded p-2 text-sm">
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              </div>
              
              <div className="mt-2 flex items-center text-xs text-gray-500">
                <span>{result.model_provider}/{result.model_name}</span>
                <span className="mx-2">•</span>
                <span>{result.processing_time_ms}ms</span>
                {result.alert_triggered && (
                  <>
                    <span className="mx-2">•</span>
                    <span className="text-red-600 font-semibold">Alert Triggered</span>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AnalysisResults;