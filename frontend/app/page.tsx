'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import io from 'socket.io-client';
import {
  Upload,
  Play,
  Download,
  Settings,
  Activity,
  Brain,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Mic,
  MessageSquare
} from 'lucide-react';

import FileUploader from '@/components/FileUploader';
import MarkerTimeline from '@/components/MarkerTimeline';
import EmotionChart from '@/components/EmotionChart';
import MarkerBadges from '@/components/MarkerBadges';
import ProfileCard from '@/components/ProfileCard';
import { analyzeContent, getSession, exportAnalysis } from '@/lib/api';
import { useMarkerStore } from '@/lib/store';

export default function MarkerEngineDashboard() {
  const [socket, setSocket] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  
  const {
    markers,
    emotions,
    profile,
    addMarker,
    setEmotions,
    setProfile,
    clearAll
  } = useMarkerStore();

  // Initialize WebSocket connection
  useEffect(() => {
    const socketInstance = io(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000', {
      path: '/ws',
      transports: ['websocket']
    });

    socketInstance.on('connect', () => {
      console.log('🔗 Connected to Marker Engine');
      toast.success('Connected to analysis engine');
    });

    socketInstance.on('marker_event', (data: any) => {
      if (data.event) {
        addMarker(data.event);
      }
    });

    socketInstance.on('analysis_complete', (data: any) => {
      setIsAnalyzing(false);
      toast.success('Analysis completed!');
      
      if (data.result) {
        setEmotions(data.result.emotions);
        setProfile(data.result.profile);
      }
    });

    socketInstance.on('disconnect', () => {
      console.log('🔌 Disconnected from Marker Engine');
      toast.error('Connection lost');
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    try {
      setIsAnalyzing(true);
      clearAll();
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/upload`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setCurrentSession(data.file_id);
        toast.success(`File uploaded: ${file.name}`);
        
        // Subscribe to WebSocket updates for this session
        if (socket) {
          socket.emit('subscribe', { session_id: data.file_id });
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload file');
      setIsAnalyzing(false);
    }
  };

  // Handle text analysis
  const handleTextAnalysis = async (text: string) => {
    try {
      setIsAnalyzing(true);
      clearAll();
      
      const sessionId = `session_${Date.now()}`;
      setCurrentSession(sessionId);
      
      // Stream analysis via WebSocket
      if (socket) {
        socket.emit('analyze_stream', {
          content: text,
          session_id: sessionId
        });
      }
      
      toast.success('Analysis started...');
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error('Failed to analyze text');
      setIsAnalyzing(false);
    }
  };

  // Handle export
  const handleExport = async (format: 'yaml' | 'json') => {
    if (!currentSession) {
      toast.error('No analysis to export');
      return;
    }
    
    try {
      const data = await exportAnalysis(currentSession, format);
      
      // Create download link
      const blob = new Blob([data.data], {
        type: format === 'yaml' ? 'application/x-yaml' : 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis_${currentSession}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export analysis');
    }
  };

  // Calculate statistics
  const stats = {
    totalMarkers: markers.length,
    levels: {
      ATO: markers.filter(m => m.level === 'ATO').length,
      SEM: markers.filter(m => m.level === 'SEM').length,
      CLU: markers.filter(m => m.level === 'CLU').length,
      MEMA: markers.filter(m => m.level === 'MEMA').length
    },
    emotionDrift: emotions?.drift_level || 'normal',
    homeBase: emotions?.home_base || 0,
    variability: emotions?.variability || 0
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-xl bg-white/5">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Brain className="w-8 h-8 text-purple-400" />
              <div>
                <h1 className="text-2xl font-bold text-white">Marker Engine</h1>
                <p className="text-purple-200 text-sm">Lean-Deep 3.2 Semantic Analysis</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {isAnalyzing && (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="flex items-center space-x-2 text-purple-400"
                >
                  <Activity className="w-5 h-5" />
                  <span className="text-sm">Analyzing...</span>
                </motion.div>
              )}
              
              <button
                onClick={() => handleExport('yaml')}
                disabled={!currentSession}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Download className="w-5 h-5 inline mr-2" />
                Export
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column - Input & Stats */}
          <div className="space-y-6">
            {/* File Upload */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20"
            >
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                <Upload className="w-5 h-5 mr-2" />
                Input Data
              </h2>
              
              <FileUploader onUpload={handleFileUpload} />
              
              <div className="mt-4">
                <textarea
                  placeholder="Or paste text here for analysis..."
                  className="w-full h-32 p-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  onBlur={(e) => {
                    if (e.target.value.trim()) {
                      handleTextAnalysis(e.target.value);
                    }
                  }}
                />
              </div>
              
              <div className="mt-4 flex items-center justify-around text-white/60 text-sm">
                <div className="flex items-center">
                  <MessageSquare className="w-4 h-4 mr-1" />
                  WhatsApp
                </div>
                <div className="flex items-center">
                  <Mic className="w-4 h-4 mr-1" />
                  Audio (.opus)
                </div>
                <div className="flex items-center">
                  <FileText className="w-4 h-4 mr-1" />
                  Text
                </div>
              </div>
            </motion.div>

            {/* Statistics */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20"
            >
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                Analysis Metrics
              </h2>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Total Markers</span>
                  <span className="text-2xl font-bold text-purple-400">{stats.totalMarkers}</span>
                </div>
                
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-white/50 mb-1">ATO</div>
                    <div className="text-xl font-semibold text-blue-400">{stats.levels.ATO}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-white/50 mb-1">SEM</div>
                    <div className="text-xl font-semibold text-green-400">{stats.levels.SEM}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-white/50 mb-1">CLU</div>
                    <div className="text-xl font-semibold text-yellow-400">{stats.levels.CLU}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-white/50 mb-1">MEMA</div>
                    <div className="text-xl font-semibold text-red-400">{stats.levels.MEMA}</div>
                  </div>
                </div>
                
                <div className="pt-3 border-t border-white/10">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white/70">Emotion Drift</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      stats.emotionDrift === 'high' ? 'bg-red-500/20 text-red-400' :
                      stats.emotionDrift === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {stats.emotionDrift.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-white/70">Home Base</span>
                    <span className="text-lg font-medium text-white">{stats.homeBase.toFixed(2)}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-white/70">Variability</span>
                    <span className="text-lg font-medium text-white">{stats.variability.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Profile Card */}
            {profile && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <ProfileCard profile={profile} />
              </motion.div>
            )}
          </div>

          {/* Center & Right Columns - Visualizations */}
          <div className="lg:col-span-2 space-y-6">
            {/* Marker Timeline */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20"
            >
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                Marker Timeline
              </h2>
              
              <MarkerTimeline markers={markers} />
            </motion.div>

            {/* Marker Badges */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20"
            >
              <h2 className="text-xl font-semibold text-white mb-4">
                Detected Markers
              </h2>
              
              <MarkerBadges markers={markers} />
            </motion.div>

            {/* Emotion Dynamics */}
            {emotions && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20"
              >
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Emotion Dynamics
                </h2>
                
                <EmotionChart emotions={emotions} />
              </motion.div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}