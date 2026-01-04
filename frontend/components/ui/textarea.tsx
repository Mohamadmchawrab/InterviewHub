import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm ring-offset-white placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171717]/10 focus-visible:ring-offset-2 focus-visible:border-[#171717] disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }

