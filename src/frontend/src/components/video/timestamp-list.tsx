'use client'

import React from 'react'
import { Clock, Play } from 'lucide-react'

interface TimestampListProps {
    videoUrl: string;
    predictions: Array<{
        frame: number;
        endFrame: number;
        timestamp: string;
        duration: string;
    }>;
    onSeek: (frame: number) => void;
}

export const TimestampList: React.FC<TimestampListProps> = ({ predictions, onSeek }) => {
    console.log('TimestampList received predictions:', predictions) // Debug log

    if (!predictions || predictions.length === 0) {
        return (
            <div className="mt-4 p-4 rounded-xl bg-slate-800/50 backdrop-blur-sm">
                <h3 className="text-white font-medium mb-3 flex items-center">
                    <Clock className="h-4 w-4 mr-2" />
                    No incidents detected
                </h3>
            </div>
        )
    }

    return (
        <div className="mt-4 p-4 rounded-xl bg-slate-800/50 backdrop-blur-sm">
            <h3 className="text-white font-medium mb-3 flex items-center">
                <Clock className="h-4 w-4 mr-2" />
                Detected Incidents ({predictions.length})
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {predictions.map((pred, index) => (
                    <button
                        key={index}
                        onClick={() => onSeek(pred.frame)}
                        className="group px-4 py-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 
                                 text-sm text-slate-300 hover:text-white transition-all
                                 flex items-center justify-between"
                    >
                        <div className="flex flex-col items-start">
                            <span className="font-medium">Incident #{index + 1}</span>
                            <span className="text-xs text-slate-400">
                                Start: {pred.timestamp}
                            </span>
                            <span className="text-xs text-slate-400">
                                Duration: {pred.duration}
                            </span>
                        </div>
                        <Play className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                ))}
            </div>
        </div>
    )
}