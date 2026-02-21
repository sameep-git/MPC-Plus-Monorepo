import { ExternalLink, Info, TriangleAlert, SquarePen } from 'lucide-react';
import { UI_CONSTANTS } from '../../constants';
import { Card } from '../ui/card';
import { cn } from '@/lib/utils'; // Good practice to use cn

interface UpdateCardProps {
    machineId?: string;
    title?: string;
    description?: string;
    iconType?: keyof typeof UI_CONSTANTS.UPDATE_ICON_TYPE;
    onClick?: () => void;
}

const defaultIcon = Info;

const iconMap: Record<string, typeof Info> = {
    [UI_CONSTANTS.UPDATE_ICON_TYPE.INFO]: Info,
    [UI_CONSTANTS.UPDATE_ICON_TYPE.SIGNOFF]: SquarePen,
    [UI_CONSTANTS.UPDATE_ICON_TYPE.THRESHOLD]: TriangleAlert,
};

const iconColorMap: Record<string, string> = {
    [UI_CONSTANTS.UPDATE_ICON_TYPE.INFO]: 'bg-primary',
    [UI_CONSTANTS.UPDATE_ICON_TYPE.THRESHOLD]: 'bg-yellow-500',
    [UI_CONSTANTS.UPDATE_ICON_TYPE.SIGNOFF]: 'bg-destructive',
};

export const UpdateCard = ({
    machineId,
    title,
    description,
    iconType = UI_CONSTANTS.UPDATE_ICON_TYPE.INFO,
    onClick
}: UpdateCardProps) => {
    const IconComponent = iconMap[iconType.toUpperCase()] || defaultIcon;
    const iconColorClass = iconColorMap[iconType] || 'bg-primary';
    const heading = machineId ? `Machine ${machineId}` : (title ?? 'Update');
    const bodyCopy = description ?? 'No additional information available.';

    return (
        <Card
            className={cn(
                "p-4 hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer",
                // Card has default padding and flex-col, we override padding here but flex-col is default.
                // We use inner div for layout so flex-col on Card is fine as long as we don't rely on it for the inner items.
                // Actually Card has `gap-6` which might affect if we have multiple children.
                // But we only have one child div.
            )}
            onClick={onClick}
        >
            <div className="flex items-start space-x-4">
                <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-1",
                    iconColorClass
                )}>
                    <IconComponent className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                    <h3 className="font-semibold mb-1">{heading}</h3>
                    <p className="text-sm text-muted-foreground">{bodyCopy}</p>
                </div>
                <ExternalLink className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-1" />
            </div>
        </Card>
    );
};
