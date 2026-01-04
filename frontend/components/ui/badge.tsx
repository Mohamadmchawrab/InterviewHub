import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2",
        {
          "border-transparent bg-foreground/10 text-foreground hover:bg-foreground/20": variant === "default",
          "border-transparent bg-foreground/5 text-foreground/80": variant === "secondary",
          "text-foreground": variant === "outline",
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }

