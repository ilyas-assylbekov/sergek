// src/components/video/video-player.tsx
'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Loader2, Play } from 'lucide-react'
import { TimestampList } from './timestamp-list'

interface VideoPlayerProps {
    videoUrl: string
    predictionsUrl?: string
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoUrl, predictionsUrl }) => {
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isMounted, setIsMounted] = useState(false)
    const [predictions, setPredictions] = useState<Array<{
    frame: number;
    endFrame: number;
    timestamp: string;
    duration: string;
}>>([]);
    const videoRef = useRef<HTMLVideoElement>(null)
    const [fps, setFps] = useState<number>(30) // Default FPS
    const [showThumbnail, setShowThumbnail] = useState(true);

    useEffect(() => {
        setIsMounted(true)
        if (predictionsUrl) {
            fetchPredictions()
        }
    }, [predictionsUrl])

    const fetchPredictions = async () => {
        try {
            if (!predictionsUrl) {
                throw new Error('predictionsUrl is undefined');
            }

            const response = await fetch(predictionsUrl);
            const data = await response.json();
            const videoFps = data.fps;
            setFps(videoFps);

            // Use the clustering function
            const clusteredPredictions = clusterPredictions(data.predictions);
            setPredictions(clusteredPredictions);

        } catch (error) {
            console.error('Error fetching predictions:', error);
            setError('Error fetching predictions');
        }
    };

    // Improved clustering function
    const clusterPredictions = (rawPredictions: any[], minGap: number = 5) => {
        if (!rawPredictions.length) return [];

        // Sort predictions by frame number
        const sortedPredictions = [...rawPredictions].sort((a, b) => a.frame - b.frame);

        const clusters: any[] = [];
        let currentCluster = {
            frame: sortedPredictions[0].frame,
            endFrame: sortedPredictions[0].frame,
            timestamp: formatTimestamp(sortedPredictions[0].frame / fps),
            duration: "0.000"
        };

        for (let i = 1; i < sortedPredictions.length; i++) {
            const currentFrame = sortedPredictions[i].frame;

            if (currentFrame - currentCluster.endFrame <= minGap) {
                // Extend current cluster
                currentCluster.endFrame = currentFrame;
                currentCluster.duration = formatTimestamp(
                    (currentFrame - currentCluster.frame) / fps
                );
            } else {
                // Start new cluster
                clusters.push(currentCluster);
                currentCluster = {
                    frame: currentFrame,
                    endFrame: currentFrame,
                    timestamp: formatTimestamp(currentFrame / fps),
                    duration: "0.000"
                };
            }
        }

        // Add final cluster
        clusters.push(currentCluster);
        return clusters;
    };

    const handleSeek = (frame: number) => {
        if (videoRef.current) {
            // Pause the video first
            videoRef.current.pause();

            // Calculate time and seek
            const timeInSeconds = frame / fps;
            videoRef.current.currentTime = timeInSeconds;

            // Scroll video into view smoothly
            videoRef.current.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    };

    const formatTimestamp = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    };

    if (!isMounted) {
        return null
    }

    return (
        <div className="space-y-4">
            <div className="relative rounded-xl overflow-hidden bg-slate-900">
                {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
                        <div className="text-white flex items-center space-x-2">
                            <Loader2 className="h-5 w-5 animate-spin" />
                            <span>Loading video...</span>
                        </div>
                    </div>
                )}

                <video
                    ref={videoRef}
                    className="w-full aspect-video"
                    controls
                    preload="metadata"
                    playsInline
                    onLoadStart={() => setIsLoading(true)}
                    onLoadedData={() => {
                        setIsLoading(false);
                        // Ensure video is paused initially
                        if (videoRef.current) {
                            videoRef.current.pause();
                        }
                    }}
                    onPlay={() => setShowThumbnail(false)}
                    onError={(e) => {
                        setError('Error loading video. Please ensure the video format is supported.')
                        setIsLoading(false)
                    }}
                >
                    <source src={videoUrl} type="video/mp4" />
                    Your browser does not support the video tag.
                </video>

                {/* Overlay for initial state */}
                {showThumbnail && !isLoading && (
                    <div
                        className="absolute inset-0 flex items-center justify-center bg-slate-900/75 cursor-pointer"
                        onClick={() => {
                            if (videoRef.current) {
                                setShowThumbnail(false);
                                videoRef.current.play();
                            }
                        }}
                    >
                        <div className="text-white flex flex-col items-center space-y-4">
                            <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center">
                                <Play className="h-8 w-8 text-white" />
                            </div>
                            <span className="text-sm font-medium">Click to play</span>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90">
                        <div className="text-red-400 text-center max-w-md px-6">
                            {error}
                        </div>
                    </div>
                )}
            </div>

            <TimestampList
                videoUrl={videoUrl}
                predictions={predictions}
                onSeek={handleSeek}
            />
        </div>
    )
}