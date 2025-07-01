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
  const [customPrompt, setCustomPrompt] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const analysisTypes = [
    { value: 'gate_detection', label: 'Gate Detection' },
    { value: 'water_level', label: 'Water Level' },
    { value: 'feed_bin_status', label: 'Feed Bin Status' },
    { value: 'animal_detection', label: 'Animal Detection' },
    { value: 'custom', label: 'Custom Analysis' },
  ];

  const defaultPrompts = {
    'gate_detection': 'Analyze this trail camera image and determine if a gate is visible. If a gate is visible, determine if it is OPEN or CLOSED. Provide detailed reasoning for your decision. Respond with JSON: {"gate_visible": boolean, "gate_open": boolean, "confidence": float between 0-1, "reasoning": "detailed explanation of what you see and why you made this decision", "visual_evidence": "specific visual details that support your conclusion"}',
    'water_level': 'Analyze this trail camera image for water troughs or containers. Estimate the water level and provide detailed reasoning. Respond with JSON: {"water_visible": boolean, "water_level": "FULL|ADEQUATE|LOW|EMPTY", "percentage_estimate": number 0-100, "confidence": float between 0-1, "reasoning": "detailed explanation of your assessment", "visual_evidence": "specific visual details about water color, reflections, container fill level"}',
    'animal_detection': 'Analyze this trail camera image for any animals. Provide detailed information about each animal detected. Respond with JSON: {"animals_detected": boolean, "animals": [{"species": "name", "count": number, "type": "livestock|wildlife", "confidence": float, "location": "where in image", "behavior": "what they are doing"}], "reasoning": "detailed explanation of identifications", "visual_evidence": "specific features used for identification"}',
    'feed_bin_status': 'Analyze this trail camera image for feed bins or feeders. Assess the feed level and condition. Respond with JSON: {"feeder_visible": boolean, "feed_level": "FULL|ADEQUATE|LOW|EMPTY", "percentage_estimate": number 0-100, "confidence": float between 0-1, "reasoning": "detailed explanation of assessment", "visual_evidence": "specific visual details about feed visibility and bin condition", "concerns": "any issues noticed"}',
    'custom': ''
  };

  useEffect(() => {
    if (showImagePicker) {
      loadImages();
    }
  }, [showImagePicker]);

  useEffect(() => {
    // Update custom prompt when analysis type changes
    if (selectedType !== 'custom') {
      setCustomPrompt(defaultPrompts[selectedType] || '');
    }
  }, [selectedType]);

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
        analysis_type: selectedType,
        custom_prompt: customPrompt
      });
      
      setResult({
        ...response.data,
        image: selectedImage
      });
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
        
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-700 mb-2"
          >
            {showAdvanced ? '▼' : '▶'} Advanced Options
          </button>
          
          {showAdvanced && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Custom Prompt
              </label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                rows={6}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                placeholder="Enter your custom analysis prompt..."
              />
              <p className="text-xs text-gray-500">
                The prompt will be sent to the AI model. Make sure to request JSON output for structured results.
              </p>
            </div>
          )}
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
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-semibold mb-3 text-lg">Analysis Result</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Image Thumbnail */}
              <div className="md:col-span-1">
                <div className="bg-gray-200 rounded-lg overflow-hidden h-48">
                  {result.image?.image_url ? (
                    <img 
                      src={result.image.image_url} 
                      alt={result.image.camera_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <i className="fa fa-image text-4xl text-gray-400"></i>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-1">{result.image?.camera_name}</p>
              </div>
              
              {/* Analysis Details */}
              <div className="md:col-span-2 space-y-2">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Analysis Type:</span>
                    <p className="font-semibold">{result.analysis_type}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Confidence:</span>
                    <p className="font-semibold">
                      <span className={`${result.confidence >= 0.8 ? 'text-green-600' : result.confidence >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {((result.result?.confidence || result.confidence) * 100).toFixed(0)}%
                      </span>
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Model:</span>
                    <p className="text-xs">{result.model_provider}/{result.model_name}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Processing Time:</span>
                    <p className="text-xs">{result.processing_time_ms}ms</p>
                  </div>
                </div>
                
                {/* Key Decision */}
                {result.result && (
                  <div className="bg-white p-3 rounded border border-gray-200">
                    <h4 className="font-medium text-sm mb-1">Decision</h4>
                    {result.result.gate_visible !== undefined && (
                      <p className="text-sm">
                        Gate: <strong>{result.result.gate_visible ? `${result.result.gate_open ? 'OPEN' : 'CLOSED'}` : 'Not Visible'}</strong>
                      </p>
                    )}
                    {result.result.water_level && (
                      <p className="text-sm">
                        Water Level: <strong>{result.result.water_level}</strong> ({result.result.percentage_estimate}%)
                      </p>
                    )}
                    {result.result.animals_detected !== undefined && (
                      <p className="text-sm">
                        Animals: <strong>{result.result.animals_detected ? `${result.result.animals.length} detected` : 'None detected'}</strong>
                      </p>
                    )}
                    {result.result.feed_level && (
                      <p className="text-sm">
                        Feed Level: <strong>{result.result.feed_level}</strong> ({result.result.percentage_estimate}%)
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
            
            {/* Reasoning and Evidence */}
            {result.result?.reasoning && (
              <div className="mb-3">
                <h4 className="font-medium text-sm mb-1">AI Reasoning</h4>
                <p className="text-sm text-gray-700 bg-white p-3 rounded border border-gray-200">
                  {result.result.reasoning}
                </p>
              </div>
            )}
            
            {result.result?.visual_evidence && (
              <div className="mb-3">
                <h4 className="font-medium text-sm mb-1">Visual Evidence</h4>
                <p className="text-sm text-gray-700 bg-white p-3 rounded border border-gray-200">
                  {result.result.visual_evidence}
                </p>
              </div>
            )}
            
            {/* Animals Detail */}
            {result.result?.animals && result.result.animals.length > 0 && (
              <div className="mb-3">
                <h4 className="font-medium text-sm mb-1">Animals Detected</h4>
                <div className="space-y-1">
                  {result.result.animals.map((animal, idx) => (
                    <div key={idx} className="text-sm bg-white p-2 rounded border border-gray-200">
                      <strong>{animal.count} {animal.species}</strong> - {animal.type}
                      {animal.location && <span className="text-gray-600"> at {animal.location}</span>}
                      {animal.behavior && <span className="text-gray-600"> ({animal.behavior})</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Concerns */}
            {result.result?.concerns && (
              <div className="mb-3">
                <h4 className="font-medium text-sm mb-1 text-orange-600">Concerns</h4>
                <p className="text-sm text-gray-700 bg-orange-50 p-3 rounded border border-orange-200">
                  {result.result.concerns}
                </p>
              </div>
            )}
            
            {/* Raw JSON (collapsible) */}
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                View Raw JSON Response
              </summary>
              <pre className="mt-2 p-3 bg-gray-800 text-gray-100 rounded text-xs overflow-x-auto">
                {JSON.stringify(result.result, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestAnalysis;