import React, { useState } from 'react';
import { Upload, CheckCircle, XCircle, AlertTriangle, Loader, Sparkles, Camera, Eye, Shield, Zap, Grid, Image } from 'lucide-react';

export default function ProductQualityControl() {
  const [mode, setMode] = useState('single');
  const [perfectImage, setPerfectImage] = useState(null);
  const [defectiveImage, setDefectiveImage] = useState(null);
  const [perfectPreview, setPerfectPreview] = useState(null);
  const [defectivePreview, setDefectivePreview] = useState(null);
  
  const [perfectAngles, setPerfectAngles] = useState({
    front: null,
    back: null,
    left: null,
    right: null
  });
  const [defectiveAngles, setDefectiveAngles] = useState({
    front: null,
    back: null,
    left: null,
    right: null
  });
  const [perfectAnglePreviews, setPerfectAnglePreviews] = useState({
    front: null,
    back: null,
    left: null,
    right: null
  });
  const [defectiveAnglePreviews, setDefectiveAnglePreviews] = useState({
    front: null,
    back: null,
    left: null,
    right: null
  });
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleImageSelect = (file, type, angle = null) => {
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      if (mode === 'single') {
        if (type === 'perfect') {
          setPerfectImage(file);
          setPerfectPreview(reader.result);
        } else {
          setDefectiveImage(file);
          setDefectivePreview(reader.result);
        }
      } else {
        if (type === 'perfect') {
          setPerfectAngles(prev => ({ ...prev, [angle]: file }));
          setPerfectAnglePreviews(prev => ({ ...prev, [angle]: reader.result }));
        } else {
          setDefectiveAngles(prev => ({ ...prev, [angle]: file }));
          setDefectiveAnglePreviews(prev => ({ ...prev, [angle]: reader.result }));
        }
      }
    };
    reader.readAsDataURL(file);
  };

  const handleCompare = async () => {
    if (mode === 'single') {
      if (!perfectImage || !defectiveImage) {
        setError('Please upload both images');
        return;
      }
    } else {
      const perfectComplete = Object.values(perfectAngles).every(img => img !== null);
      const defectiveComplete = Object.values(defectiveAngles).every(img => img !== null);
      
      if (!perfectComplete || !defectiveComplete) {
        setError('Please upload all 4 angles for both perfect and test samples');
        return;
      }
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    
    if (mode === 'single') {
      formData.append('perfect', perfectImage);
      formData.append('defective', defectiveImage);
    } else {
      formData.append('perfect_front', perfectAngles.front);
      formData.append('perfect_back', perfectAngles.back);
      formData.append('perfect_left', perfectAngles.left);
      formData.append('perfect_right', perfectAngles.right);
      
      formData.append('defective_front', defectiveAngles.front);
      formData.append('defective_back', defectiveAngles.back);
      formData.append('defective_left', defectiveAngles.left);
      formData.append('defective_right', defectiveAngles.right);
    }

    try {
      const endpoint = mode === 'single' ? '/compare' : '/compare-multiple';
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMsg = data.detail || data.error || `Server error (${res.status})`;
        throw new Error(errorMsg);
      }

      if (data.success && data.result) {
        setResult(data.result);
      } else if (data.result) {
        setResult(data.result);
      } else {
        throw new Error('Invalid response format from server');
      }

    } catch (err) {
      let errorMessage = 'An error occurred';
      
      if (err.message.includes('Failed to fetch')) {
        errorMessage = 'Cannot connect to backend. Make sure the server is running.';
      } else if (err.message.includes('NetworkError')) {
        errorMessage = 'Network error. Check your connection and CORS settings.';
      } else if (err.message.includes('404')) {
        errorMessage = 'Endpoint not found. Make sure backend supports multi-angle comparison.';
      } else if (err.message.includes('500')) {
        errorMessage = 'Server error: ' + err.message;
      } else {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPerfectImage(null);
    setDefectiveImage(null);
    setPerfectPreview(null);
    setDefectivePreview(null);
    setPerfectAngles({ front: null, back: null, left: null, right: null });
    setDefectiveAngles({ front: null, back: null, left: null, right: null });
    setPerfectAnglePreviews({ front: null, back: null, left: null, right: null });
    setDefectiveAnglePreviews({ front: null, back: null, left: null, right: null });
    setResult(null);
    setError(null);
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-emerald-600';
    if (score >= 5) return 'text-amber-600';
    return 'text-rose-600';
  };

  const getScoreBg = (score) => {
    if (score >= 8) return 'from-emerald-50 to-teal-50 border-emerald-200';
    if (score >= 5) return 'from-amber-50 to-orange-50 border-amber-200';
    return 'from-rose-50 to-red-50 border-rose-200';
  };

  const getRecommendationStyle = (recommendation) => {
    switch (recommendation) {
      case 'PASS':
        return 'from-emerald-500 to-teal-600';
      case 'FAIL':
        return 'from-rose-500 to-red-600';
      case 'REWORK':
        return 'from-amber-500 to-orange-600';
      default:
        return 'from-gray-500 to-slate-600';
    }
  };

  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'from-red-600 to-rose-700';
      case 'MAJOR':
        return 'from-orange-500 to-amber-600';
      case 'MINOR':
        return 'from-yellow-400 to-amber-500';
      default:
        return 'from-gray-500 to-slate-600';
    }
  };

  const renderAngleUpload = (type, angle, preview, displayName) => {
    const isDefective = type === 'defective';
    
    return (
      <div className="group">
        <div className="text-center mb-3">
          <span className="text-sm font-bold text-gray-700 uppercase tracking-wide">{displayName}</span>
        </div>
        {!preview ? (
          <label className={`flex flex-col items-center justify-center h-48 cursor-pointer rounded-xl border-2 border-dashed transition-all duration-300 ${
            isDefective 
              ? 'border-gray-300 hover:border-purple-500 bg-linear-to-br from-gray-50 to-purple-50/30 hover:from-purple-50 hover:to-pink-50'
              : 'border-gray-300 hover:border-emerald-500 bg-linear-to-br from-gray-50 to-emerald-50/30 hover:from-emerald-50 hover:to-teal-50'
          } group/upload`}>
            <Camera className={`w-12 h-12 transition-all duration-300 group-hover/upload:scale-110 ${
              isDefective 
                ? 'text-gray-400 group-hover/upload:text-purple-500'
                : 'text-gray-400 group-hover/upload:text-emerald-500'
            }`} />
            <p className="mt-3 text-gray-600 text-sm font-medium">Upload</p>
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => handleImageSelect(e.target.files[0], type, angle)}
            />
          </label>
        ) : (
          <div className="relative group/img">
            <div className={`absolute -inset-0.5 rounded-xl blur opacity-25 group-hover/img:opacity-50 transition-opacity ${
              isDefective
                ? 'bg-linear-to-br from-purple-500 to-pink-500'
                : 'bg-linear-to-br from-emerald-400 to-teal-500'
            }`}></div>
            <img
              src={preview}
              alt={`${type} ${angle}`}
              className="relative w-full h-48 object-cover rounded-xl border-2 border-gray-200"
            />
            <button
              onClick={() => {
                if (type === 'perfect') {
                  setPerfectAngles(prev => ({ ...prev, [angle]: null }));
                  setPerfectAnglePreviews(prev => ({ ...prev, [angle]: null }));
                } else {
                  setDefectiveAngles(prev => ({ ...prev, [angle]: null }));
                  setDefectiveAnglePreviews(prev => ({ ...prev, [angle]: null }));
                }
              }}
              className="absolute -top-2 -right-2 bg-linear-to-br from-red-500 to-rose-600 text-white p-2 rounded-full opacity-0 group-hover/img:opacity-100 transition-all duration-300 shadow-xl hover:scale-110"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-gray-50 via-blue-50 to-purple-50 relative overflow-hidden">
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl animate-float"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl animate-float-delayed"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-12 animate-fadeIn">
          <div className="inline-flex items-center justify-center gap-4 mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-linear-to-br from-blue-500 to-purple-600 blur-xl opacity-40 animate-pulse-slow"></div>
              <div className="relative p-4 bg-linear-to-br from-blue-600 to-purple-600 rounded-2xl shadow-2xl">
                <Eye className="w-12 h-12 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-5xl md:text-6xl font-bold text-gray-900 tracking-tight">
                Quality Vision AI
              </h1>
              <div className="flex items-center justify-center gap-2 mt-2">
                <Shield className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-semibold text-gray-600 uppercase tracking-wider">Enterprise Grade Quality Control</span>
              </div>
            </div>
          </div>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Leverage advanced AI-powered visual inspection to detect manufacturing defects with precision and speed
          </p>
          
          <div className="flex items-center justify-center gap-8 mt-8 flex-wrap">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">99.9%</div>
              <div className="text-sm text-gray-600 font-medium">Accuracy</div>
            </div>
            <div className="w-px h-12 bg-gray-300"></div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{"< 2s"}</div>
              <div className="text-sm text-gray-600 font-medium">Analysis Time</div>
            </div>
            <div className="w-px h-12 bg-gray-300"></div>
            <div className="text-center">
              <div className="text-3xl font-bold text-emerald-600">24/7</div>
              <div className="text-sm text-gray-600 font-medium">Availability</div>
            </div>
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="flex justify-center mb-10 animate-fadeIn">
          <div className="inline-flex bg-white rounded-2xl p-2 shadow-lg border border-gray-200">
            <button
              onClick={() => {
                setMode('single');
                handleReset();
              }}
              className={`flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-lg transition-all duration-300 ${
                mode === 'single'
                  ? 'bg-linear-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Image className="w-5 h-5" />
              Single Image
            </button>
            <button
              onClick={() => {
                setMode('multiple');
                handleReset();
              }}
              className={`flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-lg transition-all duration-300 ${
                mode === 'multiple'
                  ? 'bg-linear-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Grid className="w-5 h-5" />
              Multi-Angle (4 Views)
            </button>
          </div>
        </div>

        {/* Upload Section */}
        {mode === 'single' ? (
          <div className="grid md:grid-cols-2 gap-8 mb-10 animate-slideUp">
            {/* Perfect Image */}
            <div className="group bg-white rounded-3xl p-8 border border-gray-200 shadow-lg hover:shadow-2xl transition-all duration-500">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-linear-to-br from-emerald-400 to-teal-500 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <CheckCircle className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Reference Image</h3>
                    <p className="text-sm text-gray-500">Perfect sample standard</p>
                  </div>
                </div>
              </div>
              
              {!perfectPreview ? (
                <label className="flex flex-col items-center justify-center h-80 cursor-pointer rounded-2xl border-2 border-dashed border-gray-300 hover:border-emerald-500 transition-all duration-300 bg-linear-to-br from-gray-50 to-emerald-50/30 hover:from-emerald-50 hover:to-teal-50 group/upload">
                  <div className="relative">
                    <Camera className="w-20 h-20 text-gray-400 group-hover/upload:text-emerald-500 transition-all duration-300 group-hover/upload:scale-110" />
                    <div className="absolute -bottom-2 -right-2 bg-emerald-500 text-white rounded-full p-1 opacity-0 group-hover/upload:opacity-100 transition-opacity">
                      <Upload className="w-4 h-4" />
                    </div>
                  </div>
                  <p className="mt-6 text-gray-700 font-semibold text-lg">Upload Perfect Sample</p>
                  <p className="mt-2 text-gray-500 text-sm">PNG, JPG up to 10MB</p>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleImageSelect(e.target.files[0], 'perfect')}
                  />
                </label>
              ) : (
                <div className="relative group/img">
                  <div className="absolute -inset-1 bg-linear-to-br from-emerald-400 to-teal-500 rounded-2xl blur opacity-25 group-hover/img:opacity-50 transition-opacity"></div>
                  <img
                    src={perfectPreview}
                    alt="Perfect sample"
                    className="relative w-full h-80 object-contain rounded-2xl bg-linear-to-br from-gray-50 to-gray-100 border-2 border-gray-200 p-4"
                  />
                  <button
                    onClick={() => {
                      setPerfectImage(null);
                      setPerfectPreview(null);
                    }}
                    className="absolute -top-3 -right-3 bg-linear-to-br from-red-500 to-rose-600 text-white p-3 rounded-full opacity-0 group-hover/img:opacity-100 transition-all duration-300 shadow-xl hover:scale-110"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>

            {/* Test Image */}
            <div className="group bg-white rounded-3xl p-8 border border-gray-200 shadow-lg hover:shadow-2xl transition-all duration-500">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-linear-to-br from-purple-500 to-pink-500 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <Zap className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Test Sample</h3>
                    <p className="text-sm text-gray-500">Product to analyze</p>
                  </div>
                </div>
              </div>
              
              {!defectivePreview ? (
                <label className="flex flex-col items-center justify-center h-80 cursor-pointer rounded-2xl border-2 border-dashed border-gray-300 hover:border-purple-500 transition-all duration-300 bg-linear-to-br from-gray-50 to-purple-50/30 hover:from-purple-50 hover:to-pink-50 group/upload">
                  <div className="relative">
                    <Camera className="w-20 h-20 text-gray-400 group-hover/upload:text-purple-500 transition-all duration-300 group-hover/upload:scale-110" />
                    <div className="absolute -bottom-2 -right-2 bg-purple-500 text-white rounded-full p-1 opacity-0 group-hover/upload:opacity-100 transition-opacity">
                      <Upload className="w-4 h-4" />
                    </div>
                  </div>
                  <p className="mt-6 text-gray-700 font-semibold text-lg">Upload Test Image</p>
                  <p className="mt-2 text-gray-500 text-sm">PNG, JPG up to 10MB</p>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleImageSelect(e.target.files[0], 'defective')}
                  />
                </label>
              ) : (
                <div className="relative group/img">
                  <div className="absolute -inset-1 bg-linear-to-br from-purple-500 to-pink-500 rounded-2xl blur opacity-25 group-hover/img:opacity-50 transition-opacity"></div>
                  <img
                    src={defectivePreview}
                    alt="Test sample"
                    className="relative w-full h-80 object-contain rounded-2xl bg-linear-to-br from-gray-50 to-gray-100 border-2 border-gray-200 p-4"
                  />
                  <button
                    onClick={() => {
                      setDefectiveImage(null);
                      setDefectivePreview(null);
                    }}
                    className="absolute -top-3 -right-3 bg-linear-to-br from-red-500 to-rose-600 text-white p-3 rounded-full opacity-0 group-hover/img:opacity-100 transition-all duration-300 shadow-xl hover:scale-110"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-8 mb-10 animate-slideUp">
            {/* Perfect Angles */}
            <div className="bg-white rounded-3xl p-8 border border-gray-200 shadow-lg">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-linear-to-br from-emerald-400 to-teal-500 rounded-xl shadow-lg">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Reference Images</h3>
                  <p className="text-sm text-gray-500">4 angles of perfect sample</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                {renderAngleUpload('perfect', 'front', perfectAnglePreviews.front, 'Front')}
                {renderAngleUpload('perfect', 'back', perfectAnglePreviews.back, 'Back')}
                {renderAngleUpload('perfect', 'left', perfectAnglePreviews.left, 'Left')}
                {renderAngleUpload('perfect', 'right', perfectAnglePreviews.right, 'Right')}
              </div>
            </div>

            {/* Defective Angles */}
            <div className="bg-white rounded-3xl p-8 border border-gray-200 shadow-lg">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-linear-to-br from-purple-500 to-pink-500 rounded-xl shadow-lg">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Test Sample Images</h3>
                  <p className="text-sm text-gray-500">4 angles to analyze</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                {renderAngleUpload('defective', 'front', defectiveAnglePreviews.front, 'Front')}
                {renderAngleUpload('defective', 'back', defectiveAnglePreviews.back, 'Back')}
                {renderAngleUpload('defective', 'left', defectiveAnglePreviews.left, 'Left')}
                {renderAngleUpload('defective', 'right', defectiveAnglePreviews.right, 'Right')}
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-center gap-6 mb-10 animate-fadeIn">
          <button
            onClick={handleCompare}
            disabled={
              (mode === 'single' && (!perfectImage || !defectiveImage)) ||
              (mode === 'multiple' && 
                (!Object.values(perfectAngles).every(img => img !== null) || 
                 !Object.values(defectiveAngles).every(img => img !== null))) ||
              loading
            }
            className="group relative px-12 py-5 bg-linear-to-r from-blue-600 to-purple-600 text-white font-bold text-lg rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:hover:shadow-xl overflow-hidden"
          >
            <div className="absolute inset-0 bg-linear-to-r from-purple-600 to-pink-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative flex items-center gap-3">
              {loading ? (
                <>
                  <Loader className="w-6 h-6 animate-spin" />
                  <span>Analyzing with AI...</span>
                  <div className="ml-2 flex gap-1">
                    <span className="w-2 h-2 bg-white rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-white rounded-full animate-bounce animation-delay-200"></span>
                    <span className="w-2 h-2 bg-white rounded-full animate-bounce animation-delay-400"></span>
                  </div>
                </>
              ) : (
                <>
                  <Sparkles className="w-6 h-6 group-hover:rotate-12 transition-transform" />
                  <span>Start AI Analysis</span>
                </>
              )}
            </div>
          </button>

          {((mode === 'single' && (perfectImage || defectiveImage)) || 
            (mode === 'multiple' && (Object.values(perfectAngles).some(img => img !== null) || 
                                      Object.values(defectiveAngles).some(img => img !== null))) || 
            result) && (
            <button
              onClick={handleReset}
              className="px-12 py-5 bg-white border-2 border-gray-300 text-gray-700 font-bold text-lg rounded-2xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-300 shadow-lg"
            >
              Reset All
            </button>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-8 animate-shake">
            <div className="bg-white border-l-4 border-red-500 p-6 rounded-2xl shadow-xl">
              <div className="flex items-start gap-4">
                <div className="shrink-0 p-2 bg-red-100 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <div className="grow">
                  <h4 className="text-red-900 font-bold text-lg mb-1">Error Occurred</h4>
                  <p className="text-red-700">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="animate-slideUp">
            <div className="bg-white rounded-3xl p-10 border border-gray-200 shadow-2xl">
              <div className="flex items-center justify-center gap-3 mb-10">
                <div className="p-2 bg-linear-to-br from-blue-500 to-purple-600 rounded-xl">
                  <CheckCircle className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-4xl font-bold text-gray-900">
                  Analysis Complete
                </h2>
              </div>

              {/* Score and Verdict */}
              <div className="grid md:grid-cols-2 gap-8 mb-10">
                <div className={`rounded-2xl p-8 text-center border-2 bg-linear-to-br ${getScoreBg(result.quality_score || result.overall_score || 0)} shadow-lg hover:shadow-xl transition-shadow`}>
                  <p className="text-gray-600 mb-4 font-bold text-sm uppercase tracking-wider">Quality Score</p>
                  <div className="relative inline-block">
                    <div className={`text-8xl font-black ${getScoreColor(result.quality_score || result.overall_score || 0)} animate-scaleIn`}>
                      {result.quality_score || result.overall_score || 0}
                    </div>
                    <div className="absolute -top-2 -right-6 text-3xl font-bold text-gray-400">/10</div>
                  </div>
                  <div className="mt-4 h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full bg-linear-to-r ${(result.quality_score || result.overall_score || 0) >= 8 ? 'from-emerald-500 to-teal-500' : (result.quality_score || result.overall_score || 0) >= 5 ? 'from-amber-500 to-orange-500' : 'from-rose-500 to-red-500'} animate-progressBar`}
                      style={{ width: `${(result.quality_score || result.overall_score || 0) * 10}%` }}
                    ></div>
                  </div>
                </div>

                <div className="rounded-2xl p-8 bg-linear-to-br from-gray-50 to-gray-100 border-2 border-gray-200 flex flex-col justify-center items-center shadow-lg hover:shadow-xl transition-shadow">
                  <p className="text-gray-600 mb-6 font-bold text-sm uppercase tracking-wider">Final Verdict</p>
                  <div className={`px-10 py-4 rounded-2xl font-black text-3xl bg-linear-to-r ${getRecommendationStyle(result.recommendation || 'UNKNOWN')} text-white shadow-xl transform hover:scale-105 transition-transform animate-bounce-once`}>
                    {result.recommendation || 'UNKNOWN'}
                  </div>
                </div>
              </div>

              {/* Multi-angle specific results */}
              {mode === 'multiple' && result.angle_results && (
                <div className="mb-10">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 bg-linear-to-br from-blue-500 to-indigo-500 rounded-xl shadow-lg">
                      <Grid className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-3xl font-bold text-gray-900">Angle-by-Angle Analysis</h3>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    {Object.entries(result.angle_results).map(([angle, angleData]) => (
                      <div key={angle} className="bg-linear-to-br from-gray-50 to-blue-50/30 rounded-2xl p-6 border-2 border-gray-200 hover:shadow-lg transition-shadow">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-xl font-bold text-gray-900 uppercase">{angle} View</h4>
                          <div className={`px-4 py-2 rounded-xl font-bold text-lg ${getScoreColor(angleData.quality_score || 0)}`}>
                            {angleData.quality_score || 0}/10
                          </div>
                        </div>
                        
                        {angleData.defects && angleData.defects.length > 0 ? (
                          <div className="space-y-2">
                            {angleData.defects.map((defect, idx) => (
                              <div key={idx} className="flex items-center gap-2 text-sm">
                                <span className={`px-3 py-1 rounded-lg text-xs font-bold bg-linear-to-r ${getSeverityStyle(defect.severity)} text-white`}>
                                  {defect.severity}
                                </span>
                                <span className="text-gray-700 font-medium">{defect.name}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-emerald-600 font-semibold flex items-center gap-2">
                            <CheckCircle className="w-5 h-5" />
                            No defects detected
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Defects Section */}
              <div className="mt-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-3 bg-linear-to-br from-orange-500 to-red-500 rounded-xl shadow-lg">
                    <AlertTriangle className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-3xl font-bold text-gray-900">
                    {mode === 'multiple' ? 'All Detected Issues' : 'Detected Issues'}
                  </h3>
                </div>

                {result.defects && result.defects.length > 0 ? (
                  <div className="space-y-4">
                    {result.defects.map((defect, index) => (
                      <div
                        key={index}
                        className="group/defect flex items-start gap-5 p-6 bg-linear-to-r from-gray-50 to-orange-50/30 rounded-2xl border border-gray-200 hover:shadow-lg transition-all duration-300 animate-fadeInSequence"
                        style={{ animationDelay: `${index * 0.1}s` }}
                      >
                        <div className="shrink-0">
                          <div className="w-12 h-12 bg-linear-to-br from-orange-500 to-red-500 text-white rounded-xl flex items-center justify-center font-black text-xl shadow-lg group-hover/defect:scale-110 transition-transform">
                            {index + 1}
                          </div>
                        </div>
                        <div className="grow">
                          <p className="font-bold text-gray-900 text-xl mb-3">
                            {defect.name}
                          </p>
                          <div className="flex items-center gap-4 flex-wrap">
                            <span className={`px-4 py-2 rounded-xl text-sm font-bold bg-linear-to-r ${getSeverityStyle(defect.severity)} text-white shadow-md`}>
                              {defect.severity}
                            </span>
                            <span className="text-gray-600 font-semibold flex items-center gap-2">
                              <span className="text-xl">📍</span>
                              {defect.location}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16 bg-linear-to-br from-emerald-50 to-teal-50 rounded-2xl border-2 border-emerald-200 shadow-lg animate-scaleIn">
                    <div className="inline-block p-4 bg-linear-to-br from-emerald-500 to-teal-500 rounded-full mb-4 animate-bounce-once">
                      <CheckCircle className="w-16 h-16 text-white" />
                    </div>
                    <p className="text-emerald-700 font-bold text-2xl mb-2">
                      Perfect Quality Achieved!
                    </p>
                    <p className="text-emerald-600 text-lg">
                      No defects detected in the sample ✨
                    </p>
                  </div>
                )}
              </div>

              {/* Raw Response */}
              <details className="mt-8 bg-linear-to-br from-gray-50 to-gray-100 rounded-2xl p-6 border border-gray-200 group/details hover:shadow-lg transition-shadow">
                <summary className="cursor-pointer font-bold text-lg text-gray-700 hover:text-blue-600 transition-colors flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <span className="p-1.5 bg-blue-100 rounded-lg">
                      <Eye className="w-5 h-5 text-blue-600" />
                    </span>
                    View Detailed AI Response
                  </span>
                  <svg className="w-6 h-6 transform group-open/details:rotate-180 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </summary>
                <pre className="mt-6 p-6 bg-white rounded-xl text-sm overflow-auto border border-gray-200 text-gray-700 font-mono max-h-96 shadow-inner">
{result.raw_response || JSON.stringify(result, null, 2)}
                </pre>
              </details>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          50% { transform: translateY(-20px) translateX(10px); }
        }
        
        @keyframes float-delayed {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          50% { transform: translateY(20px) translateX(-10px); }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes scaleIn {
          from { transform: scale(0.8); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
        
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
        
        @keyframes progressBar {
          from { width: 0; }
        }
        
        @keyframes bounce-once {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        
        @keyframes fadeInSequence {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.6; }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        
        .animate-float-delayed {
          animation: float-delayed 8s ease-in-out infinite;
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.8s ease-out;
        }
        
        .animate-slideUp {
          animation: slideUp 0.6s ease-out;
        }
        
        .animate-scaleIn {
          animation: scaleIn 0.5s ease-out;
        }
        
        .animate-shake {
          animation: shake 0.5s ease-out;
        }
        
        .animate-progressBar {
          animation: progressBar 1.5s ease-out;
        }
        
        .animate-bounce-once {
          animation: bounce-once 0.6s ease-out;
        }
        
        .animate-fadeInSequence {
          animation: fadeInSequence 0.5s ease-out forwards;
          opacity: 0;
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 3s ease-in-out infinite;
        }
        
        .animation-delay-200 {
          animation-delay: 0.2s;
        }
        
        .animation-delay-400 {
          animation-delay: 0.4s;
        }
      `}</style>
    </div>
  );
}