'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { Upload, FileVideo, Clock, RefreshCw, Download, Play, X } from 'lucide-react'
import { Card } from "@/components/ui/card"
import { VideoPlayer } from './video-player'
import { Progress } from '@radix-ui/react-progress'

interface UploadStatus {
    isUploading: boolean;
    processingTime?: number;
}

interface UploadStatus {
    isUploading: boolean;
    processingTime?: number;
    status?: 'uploading' | 'processing' | 'completed' | 'error';
    processedFilename?: string;
    progress?: number;
}

export const UploadZone = () => {
    const [isDragging, setIsDragging] = useState(false)
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
        isUploading: false,
        processingTime: undefined
    })
    const [processedVideoUrl, setProcessedVideoUrl] = useState<string | null>(null)

    useEffect(() => {
        // Remove browser extension attributes after initial render
        if (typeof document !== 'undefined') {
            document.documentElement.removeAttribute('data-lt-installed')
            document.documentElement.removeAttribute('cz-shortcut-listen')
        }
    }, [])

    // Add polling function for status
    const pollProcessingStatus = useCallback(async (filename: string) => {
        try {
            const response = await fetch(`http://localhost:8000/api/videos/${filename}`)
            const data = await response.json()

            if (data.status === 'completed') {
                console.log('Processing completed:', data)
                setUploadStatus(prev => ({
                    ...prev,
                    status: 'completed',
                    processedFilename: data.processedFilename
                }))
                return true
            }

            return false
        } catch (error) {
            console.error('Error checking status:', error)
            return false
        }
    }, [])

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()

        // Only set isDragging true on dragenter/dragover
        setIsDragging(e.type === "dragenter" || e.type === "dragover")
    }, [])

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()

        // Remove any browser extension attributes
        // if (typeof document !== 'undefined') {
        //     document.documentElement.removeAttribute('data-lt-installed')
        //     document.documentElement.removeAttribute('cz-shortcut-listen')
        // }

        setIsDragging(false)

        const files = Array.from(e.dataTransfer.files)
        const videoFile = files.find(file => file.type.startsWith('video/'))

        if (videoFile) {
            setSelectedFile(videoFile)
            await handleUpload(videoFile)
        }
    }, [])

    const handleUpload = async (file: File) => {
        setUploadStatus({
            isUploading: true,
            status: 'uploading'
        })
        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch('http://localhost:8000/api/videos/upload', {
                method: 'POST',
                body: formData,
                // Add these headers
                headers: {
                    'Accept': 'application/json',
                },
                // Add credentials if needed
                credentials: 'include',
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.error || 'Upload failed')
            }

            const data = await response.json()
            setUploadStatus({
                isUploading: false,
                processingTime: data.processingTime,
                status: 'processing',
                processedFilename: data.processedFilename
            })

            // Start polling for status
            let retries = 0
            const maxRetries = 30 // 1 minute max
            while (retries < maxRetries) {
                if (await pollProcessingStatus(data.filename)) {
                    break
                }
                await new Promise(resolve => setTimeout(resolve, 2000))
                retries++
            }

        } catch (error) {
            console.error('Error uploading file:', error)
            setUploadStatus({
                isUploading: false,
                status: 'error'
            })
        }
    }

    const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files
        if (files && files[0]) {
            const file = files[0]
            if (file.type.startsWith('video/')) {
                setSelectedFile(file)
                await handleUpload(file)
            }
        }
    }, [handleUpload])

    // In upload-zone.tsx
    const handleDownload = async () => {
        console.log('Current uploadStatus:', uploadStatus);

        if (!uploadStatus.processedFilename) {
            console.log('No processed filename available');
            return;
        }

        // Use the API endpoint instead of direct file access
        const videoUrl = `http://localhost:8000/api/videos/download/${uploadStatus.processedFilename}`;
        console.log('Video URL:', videoUrl);

        try {
            // Set new video URL
            setProcessedVideoUrl(videoUrl);
            console.log('Video URL set:', videoUrl);

        } catch (error) {
            console.error('Error setting video URL:', error);
            setError('Error loading video');
        }
    }

    const predictionsUrl = uploadStatus?.status === 'completed'
        ? `http://localhost:8000/api/videos/predictions/${uploadStatus.processedFilename}`
        : undefined

    const handleReset = useCallback(() => {
        setSelectedFile(null)
        setUploadStatus({
            isUploading: false,
            processingTime: undefined
        })
        setProcessedVideoUrl(null)
        // Reset the file input
        const fileInput = document.getElementById('video-upload') as HTMLInputElement
        if (fileInput) {
            fileInput.value = ''
        }
    }, [])

    return (
        <Card className="backdrop-blur-sm bg-white/10 border-none shadow-2xl">
            <div className="p-8">
                <div
                    className={`
            relative overflow-hidden rounded-xl transition-all duration-300
            ${isDragging ? 'border-2 border-dashed border-blue-400 bg-blue-400/10' :
                            selectedFile ? 'border-2 border-dashed border-emerald-400 bg-emerald-400/10' :
                                'border-2 border-dashed border-slate-600 hover:border-slate-400'}
            p-8 text-center
          `}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('video-upload')?.click()}
                >
                    <input
                        type="file"
                        id="video-upload"
                        className="hidden"
                        accept="video/*"
                        onChange={handleFileSelect}
                    />

                    {selectedFile ? (
                        <div className="space-y-4">
                            <div className="flex items-center justify-center space-x-4">
                                <div className="p-3 rounded-full bg-emerald-400/20">
                                    <FileVideo className="h-8 w-8 text-emerald-400" />
                                </div>
                                <div className="text-left">
                                    <p className="font-medium text-white">{selectedFile.name}</p>
                                    <p className="text-sm text-slate-400">
                                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                                    </p>
                                </div>
                            </div>

                            {uploadStatus.isUploading && (
                                <div className="space-y-2">
                                    <Progress value={uploadStatus.progress} className="h-1" />
                                    <p className="text-blue-400">Uploading...</p>
                                </div>
                            )}

                            {uploadStatus.processingTime !== undefined && (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-center space-x-2 text-emerald-400">
                                        <Clock className="h-4 w-4" />
                                        <span>Processed in {uploadStatus.processingTime}s</span>
                                    </div>
                                    <button
                                        onClick={handleReset}
                                        className="px-6 py-2 rounded-full bg-blue-500 hover:bg-blue-600 text-white font-medium transition-colors duration-200"
                                    >
                                        Upload Another Video
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-emerald-400/20 blur-xl"></div>
                                <div className="relative">
                                    <Upload className="mx-auto h-16 w-16 text-slate-300" />
                                    <h3 className="mt-4 text-lg font-semibold text-white">
                                        Upload Traffic Footage
                                    </h3>
                                    <p className="mt-2 text-slate-400">
                                        Drag and drop your video file or{' '}
                                        <span className="text-blue-400 hover:text-blue-300 cursor-pointer">
                                            browse
                                        </span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {uploadStatus.status === 'processing' && (
                    <div className="mt-6 text-center">
                        <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-500/20 text-blue-400">
                            <RefreshCw className="animate-spin h-4 w-4 mr-2" />
                            Processing video...
                        </div>
                    </div>
                )}

                {uploadStatus.status === 'completed' && (
                    <div className="mt-6 space-y-6">
                        {!processedVideoUrl && (
                            <button
                                onClick={handleDownload}
                                className="w-full py-3 rounded-full bg-gradient-to-r from-blue-500 to-emerald-500 text-white font-medium hover:opacity-90 transition-opacity"
                            >
                                <Play className="h-4 w-4 inline-block mr-2" />
                                Show Processed Video
                            </button>
                        )}

                        {processedVideoUrl && (
                            <div className="space-y-6">
                                <div className="rounded-xl overflow-hidden">
                                    <VideoPlayer videoUrl={processedVideoUrl}
                                                predictionsUrl={predictionsUrl}/>
                                </div>
                                <div className="flex justify-center space-x-4">
                                    <a
                                        href={processedVideoUrl}
                                        download
                                        className="px-6 py-2 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white font-medium transition-colors duration-200"
                                    >
                                        <Download className="h-4 w-4 inline-block mr-2" />
                                        Download Video
                                    </a>
                                    <button
                                        onClick={() => setProcessedVideoUrl(null)}
                                        className="px-6 py-2 rounded-full bg-slate-700 hover:bg-slate-600 text-white font-medium transition-colors duration-200"
                                    >
                                        <X className="h-4 w-4 inline-block mr-2" />
                                        Hide Video
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {uploadStatus.status === 'error' && (
                    <div className="mt-6 text-center">
                        <div className="inline-flex items-center px-4 py-2 rounded-full bg-red-500/20 text-red-400">
                            <X className="h-4 w-4 mr-2" />
                            Error processing video
                        </div>
                    </div>
                )}
            </div>
        </Card>
    )
}

function setError(arg0: string) {
    throw new Error('Function not implemented.')
}

