import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';

const RecentImages = ({ images, loading, onAnalyze }) => {
  const [imageLoadStates, setImageLoadStates] = useState({});
  const [showThumbnails, setShowThumbnails] = useState(true);
  
  const handleImageLoad = (imageId) => {
    setImageLoadStates(prev => ({ ...prev, [imageId]: 'loaded' }));
  };
  
  const handleImageError = (imageId) => {
    setImageLoadStates(prev => ({ ...prev, [imageId]: 'error' }));
  };
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Recent Images</h2>
        <div className="text-center py-4 text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Recent Images</h2>
        <button
          onClick={() => setShowThumbnails(!showThumbnails)}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          <i className={`fa ${showThumbnails ? 'fa-th' : 'fa-list'} mr-1`}></i>
          {showThumbnails ? 'List View' : 'Grid View'}
        </button>
      </div>
      {showThumbnails ? (
        // Grid view with thumbnails
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {images.length === 0 ? (
            <div className="col-span-full text-center py-8 text-gray-500">
              <i className="fa fa-inbox text-4xl mb-2"></i>
              <p>No images found</p>
            </div>
          ) : (
            images.slice(0, 12).map((image) => (
              <div key={image.image_id} className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                <div className="aspect-w-16 aspect-h-9 bg-gray-200 relative h-32">
                  {/* Loading state */}
                  {imageLoadStates[image.image_id] !== 'loaded' && imageLoadStates[image.image_id] !== 'error' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                      <i className="fa fa-spinner fa-spin text-xl text-gray-400"></i>
                    </div>
                  )}
                  
                  {/* Image */}
                  {image.image_url && imageLoadStates[image.image_id] !== 'error' ? (
                    <img 
                      src={image.image_url} 
                      alt={image.camera_name}
                      className="w-full h-full object-cover"
                      loading="lazy"
                      onLoad={() => handleImageLoad(image.image_id)}
                      onError={() => handleImageError(image.image_id)}
                    />
                  ) : null}
                  
                  {/* Error or no URL state */}
                  {(!image.image_url || imageLoadStates[image.image_id] === 'error') && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <i className="fa fa-image text-3xl text-gray-400"></i>
                    </div>
                  )}
                  
                  {/* Status badge */}
                  <div className="absolute top-2 right-2">
                    <span className={
                      image.analysis_count > 0 
                        ? 'px-2 py-1 rounded text-xs bg-green-100 text-green-800' 
                        : 'px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800'
                    }>
                      {image.analysis_count > 0 ? 'Analyzed' : 'New'}
                    </span>
                  </div>
                </div>
                
                <div className="p-3">
                  <p className="font-medium text-sm truncate">{image.camera_name}</p>
                  <p className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(image.downloaded_at), { addSuffix: true })}
                  </p>
                  <button
                    onClick={() => onAnalyze(image.image_id)}
                    className="mt-2 w-full bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm transition-colors"
                  >
                    Analyze
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        // Table view (original)
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Camera</th>
                <th className="text-left py-2">Time</th>
                <th className="text-left py-2">Status</th>
                <th className="text-left py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {images.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center py-4 text-gray-500">
                    No images found
                  </td>
                </tr>
              ) : (
                images.map((image) => (
                  <tr key={image.image_id} className="border-b hover:bg-gray-50">
                    <td className="py-2">{image.camera_name}</td>
                    <td className="py-2">
                      {formatDistanceToNow(new Date(image.downloaded_at), { addSuffix: true })}
                    </td>
                    <td className="py-2">
                      <span className={
                        image.analysis_count > 0 
                          ? 'px-2 py-1 rounded text-xs bg-green-100 text-green-800' 
                          : 'px-2 py-1 rounded text-xs bg-gray-100 text-gray-800'
                      }>
                        {image.analysis_count > 0 ? 'Analyzed' : 'New'}
                      </span>
                    </td>
                    <td className="py-2">
                      <button
                        onClick={() => onAnalyze(image.image_id)}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                      >
                        Analyze
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default RecentImages;