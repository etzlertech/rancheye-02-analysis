import React from 'react';
import { formatDistanceToNow } from 'date-fns';

const RecentImages = ({ images, loading, onAnalyze }) => {
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
      <h2 className="text-xl font-bold mb-4">Recent Images</h2>
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
                    <span className={`px-2 py-1 rounded text-xs ${
                      image.analysis_count > 0 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
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
    </div>
  );
};

export default RecentImages;