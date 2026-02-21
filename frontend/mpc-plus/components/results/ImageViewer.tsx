'use client';

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, X, ImageOff } from 'lucide-react';
import { Button, Card } from '../ui';

export interface BeamImage {
    label: string;
    url: string;
    beamType?: string;
}

interface ImageViewerProps {
    images: BeamImage[];
    onClose: () => void;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({ images, onClose }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [imgError, setImgError] = useState<Set<number>>(new Set());

    const handlePrev = () => {
        setCurrentIndex((prev) => Math.max(0, prev - 1));
    };

    const handleNext = () => {
        setCurrentIndex((prev) => Math.min(images.length - 1, prev + 1));
    };

    const handleImageError = (index: number) => {
        setImgError((prev) => {
            const next = new Set(prev);
            next.add(index);
            return next;
        });
    };

    // Reset index when images change
    React.useEffect(() => {
        setCurrentIndex(0);
        setImgError(new Set());
    }, [images]);

    // Preload all images so navigation between them is instant
    useEffect(() => {
        images.forEach((img) => {
            const preload = new Image();
            preload.crossOrigin = 'anonymous';
            preload.src = img.url;
        });
    }, [images]);

    if (images.length === 0) {
        return (
            <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-foreground">Beam Images</h3>
                    <Button
                        onClick={onClose}
                        variant="ghost"
                        size="icon"
                        title="Close images"
                        aria-label="Close images"
                    >
                        <X className="w-5 h-5" />
                    </Button>
                </div>
                <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                    <ImageOff className="w-12 h-12 mb-3 opacity-40" />
                    <p className="text-sm">No images available for this check.</p>
                </div>
            </Card>
        );
    }

    const current = images[currentIndex];
    const hasError = imgError.has(currentIndex);

    return (
        <Card className="p-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div>
                    <h3 className="text-lg font-semibold text-foreground">Beam Images</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                        {current.beamType && <span className="font-medium">{current.beamType} — </span>}
                        {current.label}
                    </p>
                </div>
                <Button
                    onClick={onClose}
                    variant="ghost"
                    size="icon"
                    title="Close images"
                    aria-label="Close images"
                >
                    <X className="w-5 h-5" />
                </Button>
            </div>

            {/* Image Display */}
            <div className="relative bg-gray-50 rounded-lg border border-gray-200 overflow-hidden flex items-center justify-center min-h-[320px] max-h-[500px]">
                {hasError ? (
                    <div className="flex flex-col items-center text-muted-foreground">
                        <ImageOff className="w-10 h-10 mb-2 opacity-40" />
                        <p className="text-sm">Failed to load image</p>
                        <p className="text-xs mt-1 opacity-60">{current.label}</p>
                    </div>
                ) : (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                        src={current.url}
                        alt={current.label}
                        crossOrigin="anonymous"
                        className="max-w-full max-h-[480px] object-contain"
                        onError={() => handleImageError(currentIndex)}
                    />
                )}
            </div>

            {/* Pagination Controls */}
            {images.length > 1 && (
                <div className="flex items-center justify-center gap-3 mt-3">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handlePrev}
                        disabled={currentIndex === 0}
                    >
                        <ChevronLeft className="w-4 h-4 mr-1" />
                        Prev
                    </Button>
                    <span className="text-sm font-medium text-muted-foreground min-w-[80px] text-center">
                        {currentIndex + 1} of {images.length}
                    </span>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleNext}
                        disabled={currentIndex === images.length - 1}
                    >
                        Next
                        <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                </div>
            )}
        </Card>
    );
};
