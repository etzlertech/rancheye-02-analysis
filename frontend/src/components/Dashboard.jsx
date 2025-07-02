import React, { useState, useEffect } from 'react';
import Header from './Header';
import StatsCards from './StatsCards';
import RecentImages from './RecentImages';
import AnalysisResults from './AnalysisResults';
import ActiveAlerts from './ActiveAlerts';
import TestAnalysis from './TestAnalysis';
import api from '../utils/api';

const Dashboard = () => {
  const [images, setImages] = useState([]);
  const [results, setResults] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [imagesRes, resultsRes, alertsRes, configsRes] = await Promise.allSettled([
        api.get('/api/images/recent'),
        api.get('/api/analysis/results'),
        api.get('/api/alerts'),
        api.get('/api/configs'),
      ]);

      // Handle each response separately to avoid errors
      if (imagesRes.status === 'fulfilled') {
        setImages(imagesRes.value.data.images || []);
      } else {
        setImages([]);
      }
      
      if (resultsRes.status === 'fulfilled') {
        setResults(resultsRes.value.data.results || []);
      } else {
        setResults([]);
      }
      
      if (alertsRes.status === 'fulfilled') {
        setAlerts(alertsRes.value.data.alerts || []);
      } else {
        setAlerts([]);
      }
      
      if (configsRes.status === 'fulfilled') {
        setConfigs(configsRes.value.data.configs || []);
      } else {
        setConfigs([]);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setImages([]);
      setResults([]);
      setAlerts([]);
      setConfigs([]);
      setLoading(false);
    }
  };

  const [selectedImageForAnalysis, setSelectedImageForAnalysis] = useState(null);

  const handleAnalyze = async (imageId) => {
    // Find the image by ID and pass it to TestAnalysis
    const image = images.find(img => img.image_id === imageId);
    if (image) {
      setSelectedImageForAnalysis(image);
      // Scroll to top where TestAnalysis is located
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await api.post(`/api/alerts/${alertId}/acknowledge`);
      loadData();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Header />
      
      {/* Test Analysis Section - At Top */}
      <div className="mb-6">
        <TestAnalysis 
          configs={configs}
          onAnalysisComplete={loadData}
          preselectedImage={selectedImageForAnalysis}
          onImageProcessed={() => setSelectedImageForAnalysis(null)}
        />
      </div>
      
      {/* Recent Data */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <RecentImages 
            images={images} 
            loading={loading}
            onAnalyze={handleAnalyze}
          />
          <AnalysisResults 
            results={results}
            loading={loading}
          />
        </div>
        
        <div>
          <ActiveAlerts 
            alerts={alerts}
            loading={loading}
            onAcknowledge={handleAcknowledgeAlert}
          />
        </div>
      </div>
      
      {/* Stats Cards - Moved to Bottom */}
      <StatsCards />
    </div>
  );
};

export default Dashboard;