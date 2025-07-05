import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import { format, formatDistanceToNow } from 'date-fns';

const AnalysisHistory = ({ onClose }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(null);
  const [filters, setFilters] = useState({
    analysisType: '',
    modelProvider: '',
    cameraName: ''
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    totalCount: 0
  });
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    loadHistory();
  }, [filters, pagination.offset]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: pagination.limit,
        offset: pagination.offset
      });
      
      if (filters.analysisType) params.append('analysis_type', filters.analysisType);
      if (filters.modelProvider) params.append('model_provider', filters.modelProvider);
      if (filters.cameraName) params.append('camera_name', filters.cameraName);

      const response = await api.get(`/api/analysis-history?${params}`);
      setHistory(response.data.analyses);
      setSummary(response.data.summary);
      setPagination(prev => ({
        ...prev,
        totalCount: response.data.total_count
      }));
    } catch (error) {
      console.error('Error loading analysis history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newOffset) => {
    setPagination(prev => ({ ...prev, offset: newOffset }));
  };

  const getAnalysisTypeLabel = (type) => {
    const labels = {
      'wildlife_detection': 'Wildlife Detection',
      'animal_identification': 'Animal ID',
      'behavior_analysis': 'Behavior Analysis',
      'anomaly_detection': 'Anomaly Detection',
      'custom': 'Custom Analysis'
    };
    return labels[type] || type.replace('_', ' ');
  };

  const formatCost = (cost) => {
    return cost ? `$${cost.toFixed(4)}` : '$0.0000';
  };

  if (loading && history.length === 0) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-6xl max-h-[90vh] overflow-hidden">
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
      <div className="bg-white rounded-lg p-6 max-w-7xl max-h-[95vh] w-full mx-4 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Complete Analysis History</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <i className="fa fa-times text-xl"></i>
          </button>
        </div>

        {/* Summary Stats */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Analyses</p>
              <p className="text-xl font-bold">{summary.total_analyses}</p>
            </div>
            <div className="bg-green-50 p-3 rounded">
              <p className="text-sm text-gray-600">Successful</p>
              <p className="text-xl font-bold text-green-600">{summary.successful_analyses}</p>
            </div>
            <div className="bg-red-50 p-3 rounded">
              <p className="text-sm text-gray-600">Failed</p>
              <p className="text-xl font-bold text-red-600">{summary.failed_analyses}</p>
            </div>
            <div className="bg-blue-50 p-3 rounded">
              <p className="text-sm text-gray-600">Total Cost</p>
              <p className="text-xl font-bold text-blue-600">{formatCost(summary.total_cost)}</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <select
            value={filters.analysisType}
            onChange={(e) => setFilters({...filters, analysisType: e.target.value})}
            className="p-2 border rounded"
          >
            <option value="">All Analysis Types</option>
            <option value="wildlife_detection">Wildlife Detection</option>
            <option value="animal_identification">Animal ID</option>
            <option value="behavior_analysis">Behavior Analysis</option>
            <option value="anomaly_detection">Anomaly Detection</option>
            <option value="custom">Custom</option>
          </select>
          
          <select
            value={filters.modelProvider}
            onChange={(e) => setFilters({...filters, modelProvider: e.target.value})}
            className="p-2 border rounded"
          >
            <option value="">All Providers</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
          </select>
          
          <input
            type="text"
            placeholder="Filter by camera name..."
            value={filters.cameraName}
            onChange={(e) => setFilters({...filters, cameraName: e.target.value})}
            className="p-2 border rounded"
          />
        </div>

        {/* Analysis History Grid */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {history.map((item) => (
              <div
                key={item.id || item.session_id}
                className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => setSelectedImage(item)}
              >
                {/* Thumbnail */}
                <div className="relative h-48 mb-3 bg-gray-100 rounded overflow-hidden">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={`Analysis from ${item.camera_name}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = '/placeholder-image.svg';
                      }}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                      <i className="fa fa-image text-4xl"></i>
                    </div>
                  )}
                  
                  {/* Session badge */}
                  {item.is_session && (
                    <div className="absolute top-2 right-2 bg-purple-500 text-white px-2 py-1 rounded text-xs">
                      Multi-Model
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="space-y-2">
                  <p className="font-semibold text-sm truncate">
                    {item.camera_name || 'Unknown Camera'}
                  </p>
                  
                  <p className="text-xs text-gray-600">
                    {getAnalysisTypeLabel(item.analysis_type)}
                  </p>
                  
                  {item.is_session ? (
                    <div className="flex flex-wrap gap-1">
                      {item.models.map((model, idx) => (
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
                  ) : (
                    <div className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-1 rounded ${
                        item.analysis_successful ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {item.analysis_successful ? 'Success' : 'Failed'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {item.model_provider}/{item.model_name}
                      </span>
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <span>{formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}</span>
                    <span className="font-medium">
                      {formatCost(item.is_session ? item.total_cost : item.estimated_cost)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Pagination */}
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, pagination.totalCount)} of {pagination.totalCount}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(Math.max(0, pagination.offset - pagination.limit))}
              disabled={pagination.offset === 0}
              className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => handlePageChange(pagination.offset + pagination.limit)}
              disabled={pagination.offset + pagination.limit >= pagination.totalCount}
              className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>

        {/* Full Image Modal */}
        {selectedImage && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-60 p-4"
            onClick={() => setSelectedImage(null)}
          >
            <div 
              className="bg-white rounded-lg max-w-5xl max-h-[90vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-bold">Analysis Details</h3>
                  <button
                    onClick={() => setSelectedImage(null)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <i className="fa fa-times text-xl"></i>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Full size image */}
                  <div>
                    {selectedImage.image_url ? (
                      <img
                        src={selectedImage.image_url}
                        alt={`Full size from ${selectedImage.camera_name}`}
                        className="w-full rounded"
                      />
                    ) : (
                      <div className="bg-gray-100 h-96 flex items-center justify-center rounded">
                        <i className="fa fa-image text-6xl text-gray-400"></i>
                      </div>
                    )}
                  </div>

                  {/* Details */}
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-gray-600">Camera</p>
                      <p className="font-medium">{selectedImage.camera_name || 'Unknown'}</p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Analysis Type</p>
                      <p className="font-medium">{getAnalysisTypeLabel(selectedImage.analysis_type)}</p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Captured At</p>
                      <p className="font-medium">
                        {selectedImage.captured_at 
                          ? format(new Date(selectedImage.captured_at), 'PPpp')
                          : 'Unknown'}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-600">Analyzed At</p>
                      <p className="font-medium">
                        {format(new Date(selectedImage.created_at), 'PPpp')}
                      </p>
                    </div>

                    {selectedImage.is_session ? (
                      <>
                        <div>
                          <p className="text-sm text-gray-600 mb-2">Models Used</p>
                          {selectedImage.models.map((model, idx) => (
                            <div key={idx} className="mb-2 p-2 bg-gray-50 rounded">
                              <div className="flex justify-between items-center">
                                <span className="font-medium">{model.model_provider}/{model.model_name}</span>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  model.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                }`}>
                                  {model.success ? 'Success' : 'Failed'}
                                </span>
                              </div>
                              <div className="text-xs text-gray-600 mt-1">
                                {model.processing_time_ms}ms • {model.tokens_used} tokens • {formatCost(model.estimated_cost)}
                              </div>
                            </div>
                          ))}
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Total Cost</p>
                          <p className="font-medium text-lg">{formatCost(selectedImage.total_cost)}</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <p className="text-sm text-gray-600">Model</p>
                          <p className="font-medium">{selectedImage.model_provider}/{selectedImage.model_name}</p>
                        </div>

                        <div>
                          <p className="text-sm text-gray-600">Status</p>
                          <span className={`px-2 py-1 rounded text-sm ${
                            selectedImage.analysis_successful 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {selectedImage.analysis_successful ? 'Success' : 'Failed'}
                          </span>
                        </div>

                        {selectedImage.confidence && (
                          <div>
                            <p className="text-sm text-gray-600">Confidence</p>
                            <p className="font-medium">{(selectedImage.confidence * 100).toFixed(1)}%</p>
                          </div>
                        )}

                        <div>
                          <p className="text-sm text-gray-600">Performance</p>
                          <p className="font-medium">
                            {selectedImage.processing_time_ms}ms • 
                            {selectedImage.tokens_used} tokens • 
                            {formatCost(selectedImage.estimated_cost)}
                          </p>
                        </div>
                      </>
                    )}

                    {selectedImage.custom_prompt && (
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Custom Prompt</p>
                        <div className="bg-gray-50 p-2 rounded text-xs">
                          <pre className="whitespace-pre-wrap">{selectedImage.prompt_text}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisHistory;