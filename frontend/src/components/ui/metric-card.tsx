import { cn, formatScore, scoreColor, scoreBg } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: number | null | undefined;
  icon?: LucideIcon;
  invert?: boolean; // For hallucination risk (lower is better)
  suffix?: string;
  className?: string;
  rawValue?: boolean; // Show raw number instead of percentage
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  invert = false,
  suffix = "",
  className,
  rawValue = false,
}: MetricCardProps) {
  const displayValue =
    value === null || value === undefined
      ? "—"
      : rawValue
      ? value.toLocaleString() + suffix
      : formatScore(value);

  return (
    <div
      className={cn(
        "rounded-xl border bg-card p-5 shadow-sm",
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        {Icon && (
          <div className={cn("rounded-md p-1.5", scoreBg(value, invert))}>
            <Icon className={cn("h-4 w-4", scoreColor(value, invert))} />
          </div>
        )}
      </div>
      <p className={cn("text-2xl font-bold", scoreColor(value, invert))}>
        {displayValue}
      </p>
    </div>
  );
}
