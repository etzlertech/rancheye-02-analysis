import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import { formatDistanceToNow } from 'date-fns';

const ImageAnalysisHistory = ({ imageId, onClose }) => {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState(null);

  useEffect(() => {
    if (imageId) {
      loadHistory();
    }
  }, [imageId]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/images/${imageId}/analysis-history`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error loading analysis history:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionDetails = async (sessionId) => {
    try {
      const response = await api.get(`/api/images/${imageId}/analysis-history/${sessionId}`);
      setSelectedSession(response.data);
    } catch (error) {
      console.error('Error loading session details:', error);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-hidden">
          <div className="text-center py-8">
            <i className="fa fa-spinner fa-spin text-3xl text-gray-400"></i>
            <p className="text-gray-500 mt-2">Loading analysis history...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-5xl max-h-[90vh] w-full mx-4 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Analysis History</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <i className="fa fa-times text-xl"></i>
          </button>
        </div>

        {history && (
          <div className="flex-1 overflow-y-auto">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-600">Total Analyses</p>
                <p className="text-xl font-bold">{history.total_analyses}</p>
              </div>
              <div className="bg-green-50 p-3 rounded">
                <p className="text-sm text-gray-600">Successful</p>
                <p className="text-xl font-bold text-green-600">{history.successful_analyses}</p>
              </div>
              <div className="bg-red-50 p-3 rounded">
                <p className="text-sm text-gray-600">Failed</p>
                <p className="text-xl font-bold text-red-600">{history.failed_analyses}</p>
              </div>
              <div className="bg-blue-50 p-3 rounded">
                <p className="text-sm text-gray-600">Total Cost</p>
                <p className="text-xl font-bold text-blue-600">${history.total_cost.toFixed(4)}</p>
              </div>
            </div>

            {/* Analysis Types and Models Used */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded">
                <h4 className="font-semibold mb-2">Analysis Types Used</h4>
                <div className="flex flex-wrap gap-2">
                  {history.analysis_types.map(type => (
                    <span key={type} className="px-2 py-1 bg-white rounded text-sm">
                      {type.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <h4 className="font-semibold mb-2">Models Used</h4>
                <div className="flex flex-wrap gap-2">
                  {history.models_used.map(model => (
                    <span key={model} className="px-2 py-1 bg-white rounded text-sm">
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Multi-Model Sessions */}
            {history.multi_model_sessions.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Multi-Model Comparisons</h3>
                <div className="space-y-3">
                  {history.multi_model_sessions.map(session => (
                    <div key={session.session_id} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{session.analysis_type.replace('_', ' ')}</p>
                          <p className="text-sm text-gray-600">
                            {formatDistanceToNow(new Date(session.created_at), { addSuffix: true })}
                          </p>
                          <div className="flex gap-2 mt-2">
                            {session.models.map((model, idx) => (
                              <span 
                                key={idx}
                                className={`text-xs px-2 py-1 rounded ${
                                  model.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                }`}
                              >
                                {model.model_name}
                              </span>
                            ))}
                          </div>
                        </div>
                        <button
                          onClick={() => loadSessionDetails(session.session_id)}
                          className="text-blue-500 hover:text-blue-600 text-sm"
                        >
                          View Details →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Standalone Analyses */}
            {history.standalone_analyses.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Individual Analyses</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">Time</th>
                        <th className="text-left py-2">Type</th>
                        <th className="text-left py-2">Model</th>
                        <th className="text-left py-2">Status</th>
                        <th className="text-left py-2">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.standalone_analyses.map(analysis => (
                        <tr key={analysis.id} className="border-b hover:bg-gray-50">
                          <td className="py-2">
                            {formatDistanceToNow(new Date(analysis.created_at), { addSuffix: true })}
                          </td>
                          <td className="py-2">{analysis.analysis_type.replace('_', ' ')}</td>
                          <td className="py-2">{analysis.model_provider}/{analysis.model_name}</td>
                          <td className="py-2">
                            <span className={`px-2 py-1 rounded text-xs ${
                              analysis.analysis_successful 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-red-100 text-red-700'
                            }`}>
                              {analysis.analysis_successful ? 'Success' : 'Failed'}
                            </span>
                          </td>
                          <td className="py-2">${(analysis.estimated_cost || 0).toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Session Details Modal */}
        {selectedSession && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
            <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-y-auto m-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">Analysis Session Details</h3>
                <button
                  onClick={() => setSelectedSession(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <i className="fa fa-times"></i>
                </button>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600">Analysis Type</p>
                <p className="font-medium">{selectedSession.analysis_type.replace('_', ' ')}</p>
              </div>

              {selectedSession.custom_prompt && (
                <div className="mb-4 bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-600 mb-1">Custom Prompt</p>
                  <pre className="text-xs whitespace-pre-wrap">{selectedSession.prompt_text}</pre>
                </div>
              )}

              <div className="space-y-4">
                {selectedSession.model_results.map((result, idx) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-semibold">{result.model_provider} - {result.model_name}</h4>
                        <p className="text-sm text-gray-600">
                          {result.processing_time_ms}ms • 
                          {result.input_tokens && ` ${result.input_tokens} in`} • 
                          {result.output_tokens && ` ${result.output_tokens} out`} • 
                          ${(result.estimated_cost || 0).toFixed(4)}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        result.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {result.success ? 'Success' : 'Failed'}
                      </span>
                    </div>

                    {result.error_message && (
                      <div className="bg-red-50 p-2 rounded mb-2">
                        <p className="text-sm text-red-700">{result.error_message}</p>
                      </div>
                    )}

                    {result.parsed_response && (
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600 mb-1">Response</p>
                        <pre className="text-xs overflow-x-auto">
                          {JSON.stringify(result.parsed_response, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageAnalysisHistory;