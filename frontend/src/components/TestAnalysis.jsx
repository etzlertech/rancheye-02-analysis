import React, { useState } from 'react';
import toast from 'react-hot-toast';
import api from '../utils/api';

const TestAnalysis = ({ configs, onAnalysisComplete }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedType, setSelectedType] = useState('gate_detection');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const analysisTypes = [
    { value: 'gate_detection', label: 'Gate Detection' },
    { value: 'water_level', label: 'Water Level' },
    { value: 'feed_bin_status', label: 'Feed Bin Status' },
    { value: 'animal_detection', label: 'Animal Detection' },
  ];

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('analysis_type', selectedType);

    try {
      const response = await api.post('/api/upload/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setResult(response.data);
      toast.success('Analysis complete!');
      
      // Refresh data after a short delay
      setTimeout(() => {
        onAnalysisComplete();
      }, 2000);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to analyze image');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-4">Test Analysis</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Image
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Analysis Type
          </label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
          >
            {analysisTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
        
        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          className={`w-full py-2 px-4 rounded-lg font-medium ${
            !selectedFile || uploading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {uploading ? 'Analyzing...' : 'Upload & Analyze'}
        </button>
        
        {result && (
          <div className="mt-4 p-4 bg-gray-100 rounded-lg">
            <h3 className="font-semibold mb-2">Analysis Result:</h3>
            <div className="text-sm">
              <p><strong>Type:</strong> {result.analysis_type}</p>
              <p><strong>Confidence:</strong> {(result.confidence * 100).toFixed(0)}%</p>
              <p><strong>Model:</strong> {result.model_provider}/{result.model_name}</p>
              <div className="mt-2">
                <strong>Result:</strong>
                <pre className="mt-1 whitespace-pre-wrap text-xs">
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestAnalysis;