import React from 'react';
import { Button, Collapsible, CollapsibleTrigger, CollapsibleContent } from '../../components/ui';
import { ChevronDown, ChevronUp, Image as ImageIcon } from 'lucide-react';

interface CheckGroupProps {
    id: string;
    title: string;
    isExpanded: boolean;
    onToggle: (id: string) => void;
    children: React.ReactNode;
    status?: string; // Optional status (e.g., 'PASS'/'FAIL') to display in header
    className?: string; // For custom styling (e.g. background color for top-level)
    hasImages?: boolean; // Show image icon if beam has associated images
    onViewImages?: (id: string) => void; // Callback when image icon is clicked
}

export const CheckGroup: React.FC<CheckGroupProps> = ({
    id,
    title,
    isExpanded,
    onToggle,
    children,
    status,
    className = "border border-gray-100 rounded-lg",
    hasImages,
    onViewImages,
}) => {
    return (
        <Collapsible
            open={isExpanded}
            onOpenChange={() => onToggle(id)}
            className={className}
        >
            <CollapsibleTrigger asChild>
                <Button
                    variant="ghost"
                    className="w-full flex items-center justify-between p-3 h-auto hover:bg-gray-50"
                >
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-foreground">{title}</span>
                        {status && (
                            <span
                                className={`text-xs font-semibold ${status.toUpperCase() === 'PASS' ? 'text-green-600' : 'text-red-600'}`}
                            >
                                - {status.toUpperCase()}
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-1">
                        {hasImages && onViewImages && (
                            <span
                                role="button"
                                tabIndex={0}
                                aria-label={`View images for ${title}`}
                                className="inline-flex items-center justify-center h-6 w-6 rounded hover:bg-primary/10 transition-colors"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onViewImages(id);
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                        e.stopPropagation();
                                        onViewImages(id);
                                    }
                                }}
                            >
                                <ImageIcon className="w-4 h-4 text-primary" />
                            </span>
                        )}
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>
                </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
                {children}
            </CollapsibleContent>
        </Collapsible>
    );
};
