import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import api from '../utils/api';

// Helper function to calculate actual cost with proper input/output token pricing
const calculateActualCost = (modelName, inputTokens, outputTokens) => {
  // Official pricing as of 2024 (per 1M tokens)
  const costs = {
    'gpt-4o-mini': { input: 0.15, output: 0.60 },          // $0.15/$0.60 per 1M tokens
    'gpt-4o': { input: 5.00, output: 15.00 },              // $5.00/$15.00 per 1M tokens  
    'gemini-1.5-flash': { input: 0.10, output: 0.40 },     // $0.10/$0.40 per 1M tokens
    'gemini-2.0-flash-exp': { input: 0.00, output: 0.00 }, // Free during preview
    'gemini-2.5-pro': { input: 1.25, output: 10.00 }       // $1.25/$10.00 per 1M tokens (≤200k context)
  };
  
  const modelCost = costs[modelName] || { input: 0, output: 0 };
  const inputCost = (inputTokens / 1000000) * modelCost.input;
  const outputCost = (outputTokens / 1000000) * modelCost.output;
  return (inputCost + outputCost).toFixed(6);
};

// Helper function to estimate image tokens for OpenAI models
const estimateImageTokens = (imageSize = 'low') => {
  // OpenAI GPT-4o vision token calculation
  if (imageSize === 'low') {
    return 85; // Fixed cost for low detail
  }
  // For high detail: base 85 + tiles * 170
  // Assuming ~768x768 scaled image = 4 tiles for typical ranch camera images
  return 85 + (4 * 170); // = 765 tokens for high detail
};

// Component to display individual model results
const ModelResultCard = ({ result, image }) => {
  const isOpenAI = result.model_provider === 'openai';
  
  return (
    <div className={`p-4 bg-gray-50 rounded-lg border-2 ${isOpenAI ? 'border-blue-200' : 'border-purple-200'}`}>
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className={`font-semibold text-lg ${isOpenAI ? 'text-blue-700' : 'text-purple-700'}`}>
            {isOpenAI ? 'OpenAI' : 'Google Gemini'}
          </h4>
          <p className="text-sm text-gray-600">{result.model_name}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">Processing: {result.processing_time_ms}ms</p>
          <p className="text-sm text-gray-600">Tokens: {result.tokens_used || 0}</p>
          {result.tokens_used && (
            <p className="text-xs text-green-600">
              Cost: ${calculateActualCost(result.model_name, result.input_tokens || Math.floor(result.tokens_used * 0.4), result.output_tokens || Math.floor(result.tokens_used * 0.6))}
            </p>
          )}
        </div>
      </div>
      
      {result.error ? (
        <div className="bg-red-50 p-3 rounded border border-red-200">
          <p className="text-sm text-red-700">{result.error}</p>
        </div>
      ) : (
        <>
          {/* Decision Summary */}
          {result.result && (
            <div className="bg-white p-3 rounded border border-gray-200 mb-3">
              <div className="flex justify-between items-center mb-2">
                <h5 className="font-medium text-sm">Decision</h5>
                <span className={`text-sm font-semibold ${
                  result.confidence >= 0.8 ? 'text-green-600' : 
                  result.confidence >= 0.5 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  Confidence: {((result.result?.confidence || result.confidence) * 100).toFixed(0)}%
                </span>
              </div>
              
              {result.result.gate_visible !== undefined && (
                <p className="text-sm">
                  Gate: <strong>{result.result.gate_visible ? `${result.result.gate_open ? 'OPEN' : 'CLOSED'}` : 'Not Visible'}</strong>
                </p>
              )}
              {result.result.door_visible !== undefined && (
                <div className="text-sm">
                  <p>Door: <strong>{result.result.door_visible ? 'Detected' : 'Not Visible'}</strong></p>
                  {result.result.door_visible && (
                    <>
                      <p>Status: <strong>{result.result.door_open ? `OPEN (${result.result.opening_percentage}%)` : 'CLOSED'}</strong></p>
                      {result.result.door_type && <p>Type: <strong>{result.result.door_type}</strong></p>}
                    </>
                  )}
                </div>
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
          
          {/* Reasoning */}
          {result.result?.reasoning && (
            <div className="mb-3">
              <h5 className="font-medium text-sm mb-1">AI Reasoning</h5>
              <p className="text-sm text-gray-700 bg-white p-2 rounded border border-gray-200">
                {result.result.reasoning}
              </p>
            </div>
          )}
          
          {/* Visual Evidence */}
          {result.result?.visual_evidence && (
            <div className="mb-3">
              <h5 className="font-medium text-sm mb-1">Visual Evidence</h5>
              <p className="text-sm text-gray-700 bg-white p-2 rounded border border-gray-200">
                {result.result.visual_evidence}
              </p>
            </div>
          )}
          
          {/* Raw Response */}
          <details className="mt-3">
            <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
              View Raw Response
            </summary>
            <pre className="mt-2 p-2 bg-gray-800 text-gray-100 rounded text-xs overflow-x-auto">
              {result.raw_response || JSON.stringify(result.result, null, 2)}
            </pre>
          </details>
        </>
      )}
    </div>
  );
};

const TestAnalysis = ({ configs, onAnalysisComplete }) => {
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedType, setSelectedType] = useState('gate_detection');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [loadingImages, setLoadingImages] = useState(false);
  const [showImagePicker, setShowImagePicker] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [imageLoadStates, setImageLoadStates] = useState({});
  const [lastImageSync, setLastImageSync] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedModels, setSelectedModels] = useState(['openai-gpt-4o-mini']);
  const [showSavePrompt, setShowSavePrompt] = useState(false);
  const [savePromptName, setSavePromptName] = useState('');
  const [savePromptDescription, setSavePromptDescription] = useState('');
  const [saveAsDefault, setSaveAsDefault] = useState(false);
  const [customPrompts, setCustomPrompts] = useState([]);
  const [selectedCustomPrompt, setSelectedCustomPrompt] = useState(null);

  const getAnalysisTypes = () => {
    const baseTypes = [
      { value: 'gate_detection', label: 'Gate Detection' },
      { value: 'door_detection', label: 'Door Detection' },
      { value: 'water_level', label: 'Water Level' },
      { value: 'feed_bin_status', label: 'Feed Bin Status' },
      { value: 'animal_detection', label: 'Animal Detection' },
    ];

    // Add custom saved prompts
    const customTypes = customPrompts
      .filter(p => !p.is_system && !p.is_default)
      .map(p => ({
        value: `custom_${p.id}`,
        label: `📝 ${p.name}`,
        customPrompt: p
      }));

    return [
      ...baseTypes,
      ...customTypes,
      { value: 'custom', label: 'Custom Analysis' },
    ];
  };

  const analysisTypes = getAnalysisTypes();

  const modelOptions = [
    { 
      id: 'openai-gpt-4o-mini', 
      provider: 'openai',
      name: 'GPT-4o-mini',
      model: 'gpt-4o-mini',
      inputCost: 0.15, // per 1M tokens
      outputCost: 0.60  // per 1M tokens
    },
    { 
      id: 'openai-gpt-4o', 
      provider: 'openai',
      name: 'GPT-4o',
      model: 'gpt-4o',
      inputCost: 5.00, // per 1M tokens
      outputCost: 15.00  // per 1M tokens
    },
    { 
      id: 'gemini-1.5-flash', 
      provider: 'gemini',
      name: 'Gemini 1.5 Flash',
      model: 'gemini-1.5-flash',
      inputCost: 0.10, // per 1M tokens (CORRECTED)
      outputCost: 0.40  // per 1M tokens (CORRECTED)
    },
    { 
      id: 'gemini-2.0-flash', 
      provider: 'gemini',
      name: 'Gemini 2.0 Flash',
      model: 'gemini-2.0-flash-exp',
      inputCost: 0.00, // Free during preview
      outputCost: 0.00  // Free during preview
    },
    { 
      id: 'gemini-2.5-pro', 
      provider: 'gemini',
      name: 'Gemini 2.5 Pro',
      model: 'gemini-2.5-pro',
      inputCost: 1.25, // per 1M tokens (CORRECTED)
      outputCost: 10.00  // per 1M tokens (CORRECTED)
    }
  ];

  const defaultPrompts = {
    'gate_detection': `You are analyzing a trail camera image from a ranch. Look for any gates in the image and determine their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "gate_visible": true or false,
  "gate_open": true or false (null if no gate visible),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of what you see in the image and why you made this decision",
  "visual_evidence": "Specific visual details that support your conclusion (e.g., gate posts, hinges, gaps, shadows)"
}`,
    'door_detection': `You are analyzing a trail camera image from a ranch or building. Look for any doors in the image and determine their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "door_visible": true or false,
  "door_open": true or false (null if no door visible),
  "opening_percentage": 0 to 100 (estimated percentage the door is open, 0=fully closed, 100=fully open, null if not visible),
  "door_type": "barn door" or "regular door" or "sliding door" or "garage door" or "other" (null if not visible),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of what you see and how you determined the door status",
  "visual_evidence": "Specific visual details like door frame, hinges, opening gap, shadows, interior visibility"
}`,
    'water_level': `You are analyzing a trail camera image from a ranch. Look for water troughs, tanks, or containers and assess the water level.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "water_visible": true or false,
  "water_level": "FULL" or "ADEQUATE" or "LOW" or "EMPTY" (null if no water container visible),
  "percentage_estimate": 0 to 100 (null if not applicable),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of your water level assessment",
  "visual_evidence": "Specific details about water color, reflections, container fill line, or moisture marks"
}`,
    'animal_detection': `You are analyzing a trail camera image from a ranch. Identify any animals in the image.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "animals_detected": true or false,
  "animals": [
    {
      "species": "specific animal name",
      "count": number of this species visible,
      "type": "livestock" or "wildlife",
      "confidence": 0.0 to 1.0,
      "location": "where in the image (e.g., left foreground, center background)",
      "behavior": "what the animal is doing (e.g., grazing, walking, resting)"
    }
  ],
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of how you identified each animal",
  "visual_evidence": "Specific features used for identification (e.g., body shape, coloring, size)"
}`,
    'feed_bin_status': `You are analyzing a trail camera image from a ranch. Look for feed bins, feeders, or hay storage and assess their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "feeder_visible": true or false,
  "feed_level": "FULL" or "ADEQUATE" or "LOW" or "EMPTY" (null if no feeder visible),
  "percentage_estimate": 0 to 100 (null if not applicable),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of your feed level assessment",
  "visual_evidence": "Specific details about feed visibility, bin shadows, or fill indicators",
  "concerns": "Any maintenance issues, damage, or other concerns noticed (null if none)"
}`,
    'custom': ''
  };

  useEffect(() => {
    if (showImagePicker) {
      loadImages();
      // Auto-refresh images every 30 seconds while picker is open
      const interval = setInterval(() => {
        loadImages(true); // Silent refresh
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [showImagePicker]);

  useEffect(() => {
    loadCustomPrompts();
  }, []);

  const loadCustomPrompts = async () => {
    try {
      const response = await api.get('/api/prompt-templates');
      setCustomPrompts(response.data.templates || []);
    } catch (error) {
      console.error('Error loading custom prompts:', error);
      // Don't show error toast for loading - just log it
      // Table might not exist yet, which is fine
      setCustomPrompts([]);
    }
  };

  useEffect(() => {
    // Update custom prompt when analysis type changes
    if (selectedType.startsWith('custom_')) {
      // This is a saved custom prompt
      const promptId = selectedType.replace('custom_', '');
      const customPrompt = customPrompts.find(p => p.id === promptId);
      if (customPrompt) {
        setCustomPrompt(customPrompt.prompt_text);
        setSelectedCustomPrompt(customPrompt);
        setShowAdvanced(true); // Auto-expand to show the prompt
      }
    } else if (selectedType !== 'custom') {
      // This is a standard analysis type
      // Check if there's a custom default for this analysis type
      const customDefault = customPrompts.find(p => 
        p.analysis_type === selectedType && p.is_default && !p.is_system
      );
      
      if (customDefault) {
        setCustomPrompt(customDefault.prompt_text);
        setSelectedCustomPrompt(customDefault);
      } else {
        setCustomPrompt(defaultPrompts[selectedType] || '');
        setSelectedCustomPrompt(null);
      }
    } else {
      // This is 'custom' - clear the prompt
      setCustomPrompt('');
      setSelectedCustomPrompt(null);
    }
  }, [selectedType, customPrompts]);

  const handleModelToggle = (modelId) => {
    if (modelId === 'both') {
      // Select all models
      setSelectedModels(modelOptions.map(m => m.id));
    } else {
      // Toggle individual model
      setSelectedModels(prev => {
        if (prev.includes(modelId)) {
          // Don't allow deselecting all models
          if (prev.length > 1) {
            return prev.filter(id => id !== modelId);
          }
          return prev;
        } else {
          return [...prev, modelId];
        }
      });
    }
  };

  const getEstimatedCost = () => {
    // Realistic token estimation for image analysis PER MODEL
    const promptTokens = 200; // Typical analysis prompt length
    const imageTokens = 85;   // Low detail image tokens (OpenAI) / negligible for Gemini
    const outputTokensPerModel = 300; // Expected JSON response length PER MODEL
    
    let totalCost = 0;
    selectedModels.forEach(modelId => {
      const model = modelOptions.find(m => m.id === modelId);
      if (model) {
        // Input tokens = prompt + image processing (per model)
        const inputTokens = promptTokens + (model.provider === 'openai' ? imageTokens : 0);
        
        const inputCost = (inputTokens / 1000000) * model.inputCost;
        const outputCost = (outputTokensPerModel / 1000000) * model.outputCost;
        totalCost += inputCost + outputCost;
      }
    });
    
    return totalCost;
  };

  const handleSavePrompt = async () => {
    if (!savePromptName.trim() && !saveAsDefault) {
      toast.error('Please enter a name for the prompt template');
      return;
    }

    try {
      // Determine the actual analysis type for saving
      let actualAnalysisType = selectedType;
      if (selectedType.startsWith('custom_')) {
        const promptId = selectedType.replace('custom_', '');
        const customPromptObj = customPrompts.find(p => p.id === promptId);
        actualAnalysisType = customPromptObj?.analysis_type || 'custom';
      }

      const saveData = {
        name: saveAsDefault ? `Default ${actualAnalysisType.replace('_', ' ')}` : savePromptName,
        description: savePromptDescription,
        prompt_text: customPrompt,
        analysis_type: actualAnalysisType,
        save_as_default: saveAsDefault
      };

      const response = await api.post('/api/prompt-templates', saveData);
      
      if (saveAsDefault) {
        toast.success('Default prompt template updated!');
      } else {
        toast.success('Custom prompt template saved!');
      }
      
      // Reload custom prompts and close modal
      await loadCustomPrompts();
      setShowSavePrompt(false);
      setSavePromptName('');
      setSavePromptDescription('');
      setSaveAsDefault(false);
      
    } catch (error) {
      console.error('Error saving prompt:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to save prompt template';
      
      if (errorMessage.includes('custom_prompt_templates') || errorMessage.includes('does not exist')) {
        toast.error('Database setup needed. Please run the SQL from database/custom_prompt_templates.sql in Supabase dashboard.');
      } else {
        toast.error(`Failed to save prompt template: ${errorMessage}`);
      }
    }
  };

  const handlePromptChange = (newPrompt) => {
    setCustomPrompt(newPrompt);
    setSelectedCustomPrompt(null); // Clear selection when manually editing
  };

  const loadImages = async (silent = false) => {
    if (!silent) setLoadingImages(true);
    try {
      const response = await api.get('/api/images/recent?limit=100'); // Load more images
      setImages(response.data.images || []);
      setLastImageSync(new Date());
      if (!silent) {
        toast.success(`Loaded ${response.data.images?.length || 0} images`);
      }
    } catch (error) {
      console.error('Error loading images:', error);
      if (!silent) {
        toast.error('Failed to load images');
      }
    } finally {
      if (!silent) setLoadingImages(false);
    }
  };
  
  const handleImageLoad = (imageId) => {
    setImageLoadStates(prev => ({ ...prev, [imageId]: 'loaded' }));
  };
  
  const handleImageError = (imageId) => {
    setImageLoadStates(prev => ({ ...prev, [imageId]: 'error' }));
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
      // Determine the actual analysis type
      let actualAnalysisType = selectedType;
      if (selectedType.startsWith('custom_')) {
        const promptId = selectedType.replace('custom_', '');
        const customPromptObj = customPrompts.find(p => p.id === promptId);
        actualAnalysisType = customPromptObj?.analysis_type || 'custom';
        
        // Increment usage count for the template
        try {
          await api.post(`/api/prompt-templates/${promptId}/increment-usage`);
        } catch (error) {
          console.warn('Failed to increment usage count:', error);
        }
      }

      // Create a test analysis task
      const response = await api.post('/api/analysis/test', {
        image_id: selectedImage.image_id,
        analysis_type: actualAnalysisType,
        custom_prompt: customPrompt,
        selected_models: selectedModels,
        compare_models: selectedModels.length > 1
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
      <h2 className="text-xl font-bold mb-4">AI Image Analysis</h2>
      
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
                <div>
                  <h3 className="text-lg font-bold">Select Image from Storage</h3>
                  {lastImageSync && (
                    <p className="text-xs text-gray-500">
                      Last synced: {lastImageSync.toLocaleTimeString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => loadImages()}
                    disabled={loadingImages}
                    className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <i className={`fa ${loadingImages ? 'fa-spinner fa-spin' : 'fa-refresh'} mr-1"></i>
                    Refresh
                  </button>
                  <button
                    onClick={() => setShowImagePicker(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <i className="fa fa-times text-xl"></i>
                  </button>
                </div>
              </div>
              
              <div className="overflow-y-auto max-h-[60vh]">
                {loadingImages ? (
                  <div className="text-center py-8">
                    <i className="fa fa-spinner fa-spin text-2xl text-gray-400"></i>
                    <p className="text-gray-500 mt-2">Loading images...</p>
                  </div>
                ) : images.length === 0 ? (
                  <div className="text-center py-8">
                    <i className="fa fa-inbox text-4xl text-gray-400 mb-3"></i>
                    <p className="text-gray-500">No images found</p>
                    <button
                      onClick={() => loadImages()}
                      className="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                      Refresh Images
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-4">
                    {images.map((image) => (
                      <div
                        key={image.image_id}
                        onClick={() => handleSelectImage(image)}
                        className="cursor-pointer border rounded-lg p-2 hover:border-blue-500 transition-colors"
                      >
                        <div className="bg-gray-200 h-32 rounded flex items-center justify-center overflow-hidden relative">
                          {/* Loading state */}
                          {imageLoadStates[image.image_id] !== 'loaded' && imageLoadStates[image.image_id] !== 'error' && (
                            <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                              <i className="fa fa-spinner fa-spin text-2xl text-gray-400"></i>
                            </div>
                          )}
                          
                          {/* Image */}
                          {image.image_url && imageLoadStates[image.image_id] !== 'error' ? (
                            <img 
                              src={image.image_url} 
                              alt={image.camera_name}
                              className="h-full w-full object-cover"
                              loading="lazy"
                              onLoad={() => handleImageLoad(image.image_id)}
                              onError={() => handleImageError(image.image_id)}
                            />
                          ) : null}
                          
                          {/* Error or no URL state */}
                          {(!image.image_url || imageLoadStates[image.image_id] === 'error') && (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <i className="fa fa-image text-4xl text-gray-400"></i>
                            </div>
                          )}
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
        
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select AI Models
          </label>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2 mb-2">
            {modelOptions.map((model) => (
              <button
                key={model.id}
                onClick={() => handleModelToggle(model.id)}
                className={`p-3 rounded-lg border-2 transition-all ${
                  selectedModels.includes(model.id)
                    ? model.provider === 'openai' 
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-purple-500 bg-purple-50 text-purple-700'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="font-medium">{model.name}</div>
                <div className="text-xs mt-1">
                  ${((model.inputCost + model.outputCost) / 2).toFixed(2)}/1M tokens
                </div>
              </button>
            ))}
            <button
              onClick={() => handleModelToggle('both')}
              className={`p-3 rounded-lg border-2 transition-all ${
                selectedModels.length === modelOptions.length
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="font-medium">Compare All</div>
              <div className="text-xs mt-1">Side-by-side</div>
            </button>
          </div>
          
          {/* Cost Estimation */}
          <div className="bg-gray-50 p-3 rounded-lg text-sm">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Input tokens per model:</span>
              <span className="font-medium">~285 (prompt + image)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Output tokens per model:</span>
              <span className="font-medium">~300 (JSON response)</span>
            </div>
            {selectedModels.length > 1 && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total tokens:</span>
                <span className="font-medium">~{(285 + 300) * selectedModels.length} ({selectedModels.length} models)</span>
              </div>
            )}
            <div className="flex justify-between items-center mt-1 border-t pt-1">
              <span className="text-gray-600">Estimated cost:</span>
              <span className="font-medium text-green-600">
                ${getEstimatedCost().toFixed(4)}
              </span>
            </div>
            {selectedModels.length > 1 && (
              <div className="text-xs text-gray-500 mt-2">
                * Cost for {selectedModels.length} models combined
              </div>
            )}
            <div className="text-xs text-gray-500 mt-1">
              * OpenAI charges for image processing (85 tokens), Gemini includes images in text pricing
            </div>
          </div>
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
              <div className="flex justify-between items-center">
                <label className="block text-sm font-medium text-gray-700">
                  Custom Prompt
                </label>
                {customPrompt && (
                  <button
                    onClick={() => setShowSavePrompt(true)}
                    className="text-xs bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600 transition-colors"
                  >
                    💾 Save Prompt
                  </button>
                )}
              </div>
              <textarea
                value={customPrompt}
                onChange={(e) => handlePromptChange(e.target.value)}
                rows={6}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                placeholder="Enter your custom analysis prompt..."
              />
              <div className="flex justify-between items-start">
                <p className="text-xs text-gray-500">
                  The prompt will be sent to the AI model. Make sure to request JSON output for structured results.
                </p>
                {selectedCustomPrompt && (
                  <div className="text-xs text-blue-600">
                    📝 Using: {selectedCustomPrompt.name}
                  </div>
                )}
              </div>
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
        
        {result && result.compare_mode ? (
          // Compare mode results
          <div className="mt-4 space-y-4">
            <h3 className="font-semibold text-lg">Model Comparison Results</h3>
            {result.results.map((modelResult, idx) => (
              <ModelResultCard key={idx} result={modelResult} image={result.image} />
            ))}
          </div>
        ) : result ? (
          // Single model result
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
                    {result.result.door_visible !== undefined && (
                      <div className="text-sm">
                        <p>Door: <strong>{result.result.door_visible ? 'Detected' : 'Not Visible'}</strong></p>
                        {result.result.door_visible && (
                          <>
                            <p>Status: <strong>{result.result.door_open ? `OPEN (${result.result.opening_percentage}%)` : 'CLOSED'}</strong></p>
                            {result.result.door_type && <p>Type: <strong>{result.result.door_type}</strong></p>}
                          </>
                        )}
                      </div>
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
            
            {/* Error or Raw Response */}
            {result.result?.error && (
              <div className="mb-3">
                <h4 className="font-medium text-sm mb-1 text-red-600">Error</h4>
                <p className="text-sm text-gray-700 bg-red-50 p-3 rounded border border-red-200">
                  {result.result.error}
                </p>
                {result.result.raw_response && (
                  <pre className="mt-2 p-3 bg-gray-800 text-gray-100 rounded text-xs overflow-x-auto">
                    {result.result.raw_response}
                  </pre>
                )}
              </div>
            )}
            
            {/* Debug: Raw AI Response */}
            {result.raw_response && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                  View Raw AI Response
                </summary>
                <pre className="mt-2 p-3 bg-gray-800 text-gray-100 rounded text-xs overflow-x-auto">
                  {result.raw_response}
                </pre>
              </details>
            )}
            
            {/* Raw JSON (collapsible) */}
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                View Parsed JSON Response
              </summary>
              <pre className="mt-2 p-3 bg-gray-800 text-gray-100 rounded text-xs overflow-x-auto">
                {JSON.stringify(result.result, null, 2)}
              </pre>
            </details>
          </div>
        ) : null}
        
        {/* Save Prompt Modal */}
        {showSavePrompt && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold">Save Prompt Template</h3>
                <button
                  onClick={() => setShowSavePrompt(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <i className="fa fa-times text-xl"></i>
                </button>
              </div>
              
              <div className="space-y-4">
                {/* Save as Default Toggle */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="saveAsDefault"
                    checked={saveAsDefault}
                    onChange={(e) => setSaveAsDefault(e.target.checked)}
                    className="mr-2"
                  />
                  <label htmlFor="saveAsDefault" className="text-sm">
                    Save as default for {analysisTypes.find(t => t.value === selectedType)?.label}
                  </label>
                </div>
                
                {!saveAsDefault && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Template Name *
                      </label>
                      <input
                        type="text"
                        value={savePromptName}
                        onChange={(e) => setSavePromptName(e.target.value)}
                        className="w-full border border-gray-300 rounded px-3 py-2"
                        placeholder="Enter template name..."
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description (optional)
                      </label>
                      <textarea
                        value={savePromptDescription}
                        onChange={(e) => setSavePromptDescription(e.target.value)}
                        rows={2}
                        className="w-full border border-gray-300 rounded px-3 py-2"
                        placeholder="Describe what this template is used for..."
                      />
                    </div>
                  </>
                )}
                
                <div className="bg-gray-50 p-3 rounded text-sm">
                  <strong>Analysis Type:</strong> {analysisTypes.find(t => t.value === selectedType)?.label}
                  <br />
                  <strong>Prompt Length:</strong> {customPrompt.length} characters
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowSavePrompt(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSavePrompt}
                    disabled={!saveAsDefault && !savePromptName.trim()}
                    className={`flex-1 px-4 py-2 rounded text-white ${
                      (!saveAsDefault && !savePromptName.trim())
                        ? 'bg-gray-300 cursor-not-allowed'
                        : 'bg-green-500 hover:bg-green-600'
                    }`}
                  >
                    {saveAsDefault ? 'Save as Default' : 'Save Copy'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestAnalysis;