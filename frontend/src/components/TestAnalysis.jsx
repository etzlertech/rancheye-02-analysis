import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import api from '../utils/api';

const TestAnalysis = ({ configs, onAnalysisComplete }) => {
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedType, setSelectedType] = useState('gate_detection');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [loadingImages, setLoadingImages] = useState(false);
  const [showImagePicker, setShowImagePicker] = useState(false);

  const analysisTypes = [
    { value: 'gate_detection', label: 'Gate Detection' },
    { value: 'water_level', label: 'Water Level' },
    { value: 'feed_bin_status', label: 'Feed Bin Status' },
    { value: 'animal_detection', label: 'Animal Detection' },
  ];

  useEffect(() => {
    if (showImagePicker) {
      loadImages();
    }
  }, [showImagePicker]);

  const loadImages = async () => {
    setLoadingImages(true);
    try {
      const response = await api.get('/api/images/recent?limit=50');
      setImages(response.data.images || []);
    } catch (error) {
      console.error('Error loading images:', error);
      toast.error('Failed to load images');
    } finally {
      setLoadingImages(false);
    }
  };

  const handleSelectImage = (image) => {
    setSelectedImage(image);
    setShowImagePicker(false);
    setResult(null);
  };

  const handleAnalyze = async () => {
    if (!selectedImage) {
      toast.error('Please select an image');
      return;
    }

    setAnalyzing(true);

    try {
      // Create a test analysis task
      const response = await api.post('/api/analysis/test', {
        image_id: selectedImage.image_id,
        analysis_type: selectedType
      });
      
      setResult(response.data);
      toast.success('Analysis complete!');
      
      // Refresh data after a short delay
      setTimeout(() => {
        onAnalysisComplete();
      }, 2000);
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error('Failed to analyze image');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-4">Test Analysis</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Image from Storage
          </label>
          {selectedImage ? (
            <div className="border rounded-lg p-3 bg-gray-50">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-medium">{selectedImage.camera_name}</p>
                  <p className="text-sm text-gray-600">{selectedImage.image_id}</p>
                </div>
                <button
                  onClick={() => setShowImagePicker(true)}
                  className="text-blue-500 hover:text-blue-600 text-sm"
                >
                  Change
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowImagePicker(true)}
              className="w-full border-2 border-dashed border-gray-300 rounded-lg py-4 hover:border-gray-400 transition-colors"
            >
              <div className="text-center">
                <i className="fa fa-database text-gray-400 text-3xl mb-2"></i>
                <p className="text-gray-600 font-medium">Browse Supabase Storage</p>
                <p className="text-gray-500 text-sm mt-1">Select from captured images</p>
              </div>
            </button>
          )}
        </div>

        {showImagePicker && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-hidden">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold">Select Image from Storage</h3>
                <button
                  onClick={() => setShowImagePicker(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <i className="fa fa-times text-xl"></i>
                </button>
              </div>
              
              <div className="overflow-y-auto max-h-[60vh]">
                {loadingImages ? (
                  <div className="text-center py-8">
                    <i className="fa fa-spinner fa-spin text-2xl text-gray-400"></i>
                    <p className="text-gray-500 mt-2">Loading images...</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-4">
                    {images.map((image) => (
                      <div
                        key={image.image_id}
                        onClick={() => handleSelectImage(image)}
                        className="cursor-pointer border rounded-lg p-2 hover:border-blue-500 transition-colors"
                      >
                        <div className="bg-gray-200 h-32 rounded flex items-center justify-center overflow-hidden">
                          {image.image_url ? (
                            <img 
                              src={image.image_url} 
                              alt={image.camera_name}
                              className="h-full w-full object-cover"
                              onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'block';
                              }}
                            />
                          ) : null}
                          <i className="fa fa-image text-4xl text-gray-400" style={{display: image.image_url ? 'none' : 'block'}}></i>
                        </div>
                        <p className="text-sm font-medium mt-2 truncate">{image.camera_name}</p>
                        <p className="text-xs text-gray-500 truncate">{image.image_id}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        
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
          onClick={handleAnalyze}
          disabled={!selectedImage || analyzing}
          className={`w-full py-2 px-4 rounded-lg font-medium ${
            !selectedImage || analyzing
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {analyzing ? 'Analyzing...' : 'Analyze Image'}
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