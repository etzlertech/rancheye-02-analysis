import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import { format, formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

const AnalysisHistory = ({ onClose }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedImages, setExpandedImages] = useState(new Set());
  const [filters, setFilters] = useState({
    analysisType: '',
    modelProvider: '',
    cameraName: '',
    dateRange: 'all'
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    totalCount: 0
  });
  const [summary, setSummary] = useState(null);
  const [selectedResponse, setSelectedResponse] = useState(null);
  const [editingNotes, setEditingNotes] = useState({});
  const [savingStates, setSavingStates] = useState({});

  // Group analyses by image
  const [groupedData, setGroupedData] = useState({});

  useEffect(() => {
    loadHistory();
  }, [filters, pagination.offset]);

  useEffect(() => {
    // Group analyses by image_id
    const grouped = {};
    
    if (!history || history.length === 0) {
      setGroupedData({});
      return;
    }
    
    history.forEach((item) => {
      const imageId = item.image_id;
      if (!imageId) return;
      
      if (!grouped[imageId]) {
        grouped[imageId] = {
          image_id: imageId,
          image_url: item.image_url,
          camera_name: item.camera_name,
          captured_at: item.captured_at,
          analyses: []
        };
      }
      
      if (item.is_session && item.models) {
        // For multi-model sessions, expand each model into a separate analysis
        item.models.forEach(model => {
          grouped[imageId].analyses.push({
            id: model.id || `${item.session_id}-${model.model_name}`,
            image_id: imageId,
            image_url: item.image_url,
            camera_name: item.camera_name,
            captured_at: item.captured_at,
            created_at: item.created_at,
            analysis_type: item.analysis_type,
            model_provider: model.model_provider,
            model_name: model.model_name,
            analysis_successful: model.success,
            confidence: model.confidence,
            tokens_used: model.tokens_used,
            estimated_cost: model.estimated_cost,
            processing_time_ms: model.processing_time_ms,
            prompt_text: item.prompt_text,
            custom_prompt: item.custom_prompt,
            quality_rating: model.quality_rating,
            user_notes: model.user_notes,
            parsed_response: model.parsed_response,
            session_id: item.session_id
          });
        });
      } else if (!item.is_session) {
        // Individual analysis
        grouped[imageId].analyses.push(item);
      }
    });
    
    setGroupedData(grouped);
    
    // Auto-expand first image for better UX
    if (Object.keys(grouped).length > 0 && expandedImages.size === 0) {
      const firstImageId = Object.keys(grouped)[0];
      setExpandedImages(new Set([firstImageId]));
    }
  }, [history]);

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
      setHistory(response.data.analyses || []);
      setSummary(response.data.summary || {});
      setPagination(prev => ({
        ...prev,
        totalCount: response.data.total_count || 0
      }));
    } catch (error) {
      console.error('Error loading analysis history:', error);
      toast.error('Failed to load analysis history');
    } finally {
      setLoading(false);
    }
  };

  const toggleImageExpanded = (imageId) => {
    const newExpanded = new Set(expandedImages);
    if (newExpanded.has(imageId)) {
      newExpanded.delete(imageId);
    } else {
      newExpanded.add(imageId);
    }
    setExpandedImages(newExpanded);
  };

  const updateRating = async (analysisId, rating) => {
    setSavingStates(prev => ({ ...prev, [`rating-${analysisId}`]: true }));
    try {
      await api.patch(`/api/analysis/${analysisId}/rating`, { quality_rating: rating });
      
      // Update local state
      setHistory(prev => prev.map(item => 
        item.id === analysisId ? { ...item, quality_rating: rating } : item
      ));
      
      toast.success('Rating updated');
    } catch (error) {
      console.error('Error updating rating:', error);
      toast.error('Failed to update rating');
    } finally {
      setSavingStates(prev => ({ ...prev, [`rating-${analysisId}`]: false }));
    }
  };

  const updateNotes = async (analysisId) => {
    const notes = editingNotes[analysisId] || '';
    setSavingStates(prev => ({ ...prev, [`notes-${analysisId}`]: true }));
    
    try {
      await api.patch(`/api/analysis/${analysisId}/notes`, { user_notes: notes });
      
      // Update local state
      setHistory(prev => prev.map(item => 
        item.id === analysisId ? { ...item, user_notes: notes } : item
      ));
      
      toast.success('Notes saved');
    } catch (error) {
      console.error('Error updating notes:', error);
      toast.error('Failed to save notes');
    } finally {
      setSavingStates(prev => ({ ...prev, [`notes-${analysisId}`]: false }));
    }
  };

  const StarRating = ({ value, onChange, analysisId }) => {
    const [hover, setHover] = useState(0);
    const saving = savingStates[`rating-${analysisId}`];
    
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => onChange(star)}
            onMouseEnter={() => setHover(star)}
            onMouseLeave={() => setHover(0)}
            disabled={saving}
            className={`text-lg transition-colors ${
              saving ? 'cursor-wait' : 'cursor-pointer'
            }`}
          >
            <i 
              className={`fa fa-star ${
                (hover || value || 0) >= star 
                  ? 'text-yellow-400' 
                  : 'text-gray-300'
              }`}
            />
          </button>
        ))}
        {saving && <i className="fa fa-spinner fa-spin text-sm text-gray-500 ml-1" />}
      </div>
    );
  };

  const truncateText = (text, maxLength) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const formatCost = (cost) => {
    return cost ? `$${cost.toFixed(4)}` : '$0.0000';
  };

  const getAnalysisTypeLabel = (type) => {
    const labels = {
      'wildlife_detection': 'Wildlife',
      'animal_identification': 'Animal ID',
      'behavior_analysis': 'Behavior',
      'anomaly_detection': 'Anomaly',
      'water_level': 'Water Level',
      'custom': 'Custom'
    };
    return labels[type] || type.replace('_', ' ');
  };

  if (loading && Object.keys(groupedData).length === 0) {
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
      <div className="bg-white rounded-lg p-6 max-w-[95vw] max-h-[95vh] w-full mx-4 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Analysis History - Grid View</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <i className="fa fa-times text-xl"></i>
          </button>
        </div>

        {/* Summary Stats */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
          <select
            value={filters.analysisType}
            onChange={(e) => setFilters({...filters, analysisType: e.target.value})}
            className="p-2 border rounded text-sm"
          >
            <option value="">All Analysis Types</option>
            <option value="wildlife_detection">Wildlife Detection</option>
            <option value="animal_identification">Animal ID</option>
            <option value="behavior_analysis">Behavior Analysis</option>
            <option value="anomaly_detection">Anomaly Detection</option>
            <option value="water_level">Water Level</option>
            <option value="custom">Custom</option>
          </select>
          
          <select
            value={filters.modelProvider}
            onChange={(e) => setFilters({...filters, modelProvider: e.target.value})}
            className="p-2 border rounded text-sm"
          >
            <option value="">All Providers</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="gemini">Gemini</option>
          </select>
          
          <input
            type="text"
            placeholder="Filter by camera name..."
            value={filters.cameraName}
            onChange={(e) => setFilters({...filters, cameraName: e.target.value})}
            className="p-2 border rounded text-sm"
          />
          
          <button
            onClick={() => setExpandedImages(new Set(Object.keys(groupedData)))}
            className="p-2 bg-gray-100 rounded text-sm hover:bg-gray-200"
          >
            <i className="fa fa-expand mr-1"></i> Expand All
          </button>
        </div>

        {/* Main Content - Grouped Grid */}
        <div className="flex-1 overflow-y-auto">
          {Object.keys(groupedData).length === 0 ? (
            <div className="text-center py-12">
              <i className="fa fa-folder-open text-6xl text-gray-300 mb-4"></i>
              <p className="text-lg text-gray-500">No analysis history found</p>
              <p className="text-sm text-gray-400 mt-2">Try adjusting your filters or run some analyses first</p>
            </div>
          ) : (
            <>
              {expandedImages.size === 0 && (
                <div className="text-center py-4 mb-4 bg-blue-50 rounded">
                  <p className="text-blue-700">
                    Found {Object.keys(groupedData).length} images with analyses. 
                    Click on an image to expand and see details, or use "Expand All" button above.
                  </p>
                </div>
              )}
              {Object.entries(groupedData).map(([imageId, imageData]) => {
            const isExpanded = expandedImages.has(imageId);
            const analyses = imageData.analyses;
            const successCount = analyses.filter(a => a.analysis_successful).length;
            const totalCost = analyses.reduce((sum, a) => sum + (a.estimated_cost || 0), 0);
            const avgRating = analyses.filter(a => a.quality_rating).reduce((sum, a, _, arr) => 
              sum + a.quality_rating / arr.length, 0
            );

            return (
              <div key={imageId} className="mb-4 border rounded-lg shadow-sm">
                {/* Image Header */}
                <div 
                  className="bg-gray-50 p-4 cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleImageExpanded(imageId)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Thumbnail */}
                      <div className="w-20 h-20 bg-gray-200 rounded overflow-hidden flex-shrink-0">
                        {imageData.image_url ? (
                          <img 
                            src={imageData.image_url} 
                            alt={imageData.camera_name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.src = '/placeholder-image.svg';
                            }}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <i className="fa fa-image text-gray-400"></i>
                          </div>
                        )}
                      </div>
                      
                      {/* Image Info */}
                      <div>
                        <h3 className="font-semibold">
                          <i className="fa fa-camera mr-1"></i>
                          {imageData.camera_name || 'Unknown Camera'}
                        </h3>
                        <p className="text-sm text-gray-600">
                          Captured: {imageData.captured_at 
                            ? format(new Date(imageData.captured_at), 'PPpp')
                            : 'Unknown'}
                        </p>
                        <div className="flex gap-4 mt-1 text-sm">
                          <span>
                            {analyses.length} analyses
                          </span>
                          <span className="text-green-600">
                            {successCount}/{analyses.length} successful
                          </span>
                          <span className="text-blue-600">
                            Total: {formatCost(totalCost)}
                          </span>
                          {avgRating > 0 && (
                            <span className="text-yellow-600">
                              Avg: {avgRating.toFixed(1)} ⭐
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <i className={`fa fa-chevron-${isExpanded ? 'up' : 'down'} text-gray-400`}></i>
                  </div>
                </div>

                {/* Analysis Grid */}
                {isExpanded && (
                  <div className="p-4 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left">
                          <th className="p-2">Time</th>
                          <th className="p-2">Type</th>
                          <th className="p-2">Model</th>
                          <th className="p-2">Status</th>
                          <th className="p-2">Conf</th>
                          <th className="p-2 min-w-[200px]">Prompt</th>
                          <th className="p-2 min-w-[200px]">Response</th>
                          <th className="p-2">Rating</th>
                          <th className="p-2 min-w-[200px]">Notes</th>
                          <th className="p-2">Tokens</th>
                          <th className="p-2">Cost</th>
                          <th className="p-2">Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analyses.map((analysis) => (
                          <tr key={analysis.id} className="border-b hover:bg-gray-50">
                            <td className="p-2">
                              {formatDistanceToNow(new Date(analysis.created_at), { addSuffix: true })}
                            </td>
                            <td className="p-2">{getAnalysisTypeLabel(analysis.analysis_type)}</td>
                            <td className="p-2">{analysis.model_provider}/{analysis.model_name}</td>
                            <td className="p-2">
                              <span className={`px-2 py-1 rounded text-xs ${
                                analysis.analysis_successful 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-red-100 text-red-700'
                              }`}>
                                {analysis.analysis_successful ? '✓ Success' : '✗ Failed'}
                              </span>
                            </td>
                            <td className="p-2">
                              {analysis.confidence 
                                ? `${(analysis.confidence * 100).toFixed(0)}%`
                                : '-'}
                            </td>
                            <td className="p-2">
                              <button
                                className="text-blue-500 hover:underline text-left"
                                onClick={() => setSelectedResponse({ 
                                  ...analysis, 
                                  showPrompt: true 
                                })}
                              >
                                {truncateText(analysis.prompt_text, 50)}
                              </button>
                            </td>
                            <td className="p-2">
                              <button
                                className="text-blue-500 hover:underline text-left"
                                onClick={() => setSelectedResponse({ 
                                  ...analysis, 
                                  showResponse: true 
                                })}
                              >
                                {analysis.parsed_response 
                                  ? truncateText(JSON.stringify(analysis.parsed_response), 50)
                                  : 'No response'}
                              </button>
                            </td>
                            <td className="p-2">
                              <StarRating 
                                value={analysis.quality_rating} 
                                onChange={(rating) => updateRating(analysis.id, rating)}
                                analysisId={analysis.id}
                              />
                            </td>
                            <td className="p-2">
                              <div className="flex items-center gap-1">
                                <textarea
                                  value={editingNotes[analysis.id] !== undefined 
                                    ? editingNotes[analysis.id] 
                                    : analysis.user_notes || ''}
                                  onChange={(e) => setEditingNotes(prev => ({
                                    ...prev,
                                    [analysis.id]: e.target.value
                                  }))}
                                  onBlur={() => updateNotes(analysis.id)}
                                  placeholder="Add notes..."
                                  className="w-full p-1 border rounded text-xs resize-none"
                                  rows="2"
                                />
                                {savingStates[`notes-${analysis.id}`] && (
                                  <i className="fa fa-spinner fa-spin text-sm text-gray-500" />
                                )}
                              </div>
                            </td>
                            <td className="p-2 text-xs">
                              {analysis.tokens_used || '-'}
                            </td>
                            <td className="p-2 text-xs">
                              {formatCost(analysis.estimated_cost)}
                            </td>
                            <td className="p-2 text-xs">
                              {analysis.processing_time_ms}ms
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
            </>
          )}
        </div>

        {/* Pagination */}
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, pagination.totalCount)} of {pagination.totalCount}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
              disabled={pagination.offset === 0}
              className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
              disabled={pagination.offset + pagination.limit >= pagination.totalCount}
              className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>

        {/* Response Detail Modal */}
        {selectedResponse && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 p-4"
            onClick={() => setSelectedResponse(null)}
          >
            <div 
              className="bg-white rounded-lg max-w-4xl max-h-[80vh] overflow-auto p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold">
                  {selectedResponse.showPrompt ? 'Prompt Details' : 'Response Details'}
                </h3>
                <button
                  onClick={() => setSelectedResponse(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <i className="fa fa-times"></i>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Model</p>
                  <p className="font-medium">{selectedResponse.model_provider}/{selectedResponse.model_name}</p>
                </div>

                {selectedResponse.showPrompt && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Full Prompt</p>
                    <pre className="bg-gray-50 p-4 rounded text-sm whitespace-pre-wrap">
                      {selectedResponse.prompt_text}
                    </pre>
                  </div>
                )}

                {selectedResponse.showResponse && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Full Response</p>
                    <pre className="bg-gray-50 p-4 rounded text-sm whitespace-pre-wrap overflow-x-auto">
                      {selectedResponse.parsed_response 
                        ? JSON.stringify(selectedResponse.parsed_response, null, 2)
                        : selectedResponse.raw_response || 'No response data'}
                    </pre>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Processing Time</p>
                    <p className="font-medium">{selectedResponse.processing_time_ms}ms</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Tokens Used</p>
                    <p className="font-medium">{selectedResponse.tokens_used || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Cost</p>
                    <p className="font-medium">{formatCost(selectedResponse.estimated_cost)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Confidence</p>
                    <p className="font-medium">
                      {selectedResponse.confidence 
                        ? `${(selectedResponse.confidence * 100).toFixed(1)}%`
                        : 'N/A'}
                    </p>
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