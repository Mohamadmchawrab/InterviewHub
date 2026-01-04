import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "secondary"
  size?: "default" | "sm" | "lg"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 shadow-sm hover:shadow-md",
          {
            "bg-[#171717] text-white hover:bg-[#2a2a2a] active:scale-[0.98]": variant === "default",
            "border border-gray-300 bg-transparent hover:bg-gray-50 text-gray-700": variant === "outline",
            "hover:bg-gray-100 text-gray-700": variant === "ghost",
            "bg-gray-100 hover:bg-gray-200 text-gray-900": variant === "secondary",
            "h-11 px-6 py-2.5": size === "default",
            "h-9 px-4 py-2": size === "sm",
            "h-12 px-8 py-3": size === "lg",
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }

