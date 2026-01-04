"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { createSession } from "@/lib/api"
import { Sparkles, GraduationCap, Target, Zap } from "lucide-react"

const EXAMPLE_INTERVIEWS = [
  { text: "I have a frontend interview in 10 days", type: "interview" },
  { text: "I have a backend developer interview next week", type: "interview" },
  { text: "Full-stack engineer interview coming up", type: "interview" },
  { text: "I have a data science interview in 2 weeks", type: "interview" },
  { text: "Product manager interview next month", type: "interview" },
  { text: "UX designer interview in 5 days", type: "interview" },
]

export default function HomePage() {
  const [userGoal, setUserGoal] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userGoal.trim()) return

    setIsLoading(true)
    try {
      const response = await createSession({ user_goal_text: userGoal })
      // Clear the input
      setUserGoal("")
      router.push(`/session/${response.session_id}`)
    } catch (error) {
      console.error("Failed to create session:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to create session. Please try again."
      alert(errorMessage)
      setIsLoading(false)
    }
  }

  const handleExampleClick = (example: string) => {
    setUserGoal(example)
  }

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden ml-0 lg:ml-64">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-100">
      </div>

      {/* Content */}
      <div className="relative z-10 flex-1 flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 pt-12 pb-8 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Sparkles className="h-8 w-8 text-gray-800" />
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900">
                InterviewHub
              </h1>
            </div>
            <p className="text-lg text-gray-700 mb-2">
              AI-Powered Interview Preparation Assistant
            </p>
            <p className="text-sm text-gray-600 max-w-2xl mx-auto">
              Transform your interview preparation into a structured, actionable plan. 
              Get personalized checklists, practice with AI interviews, and boost your confidence.
            </p>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col items-center justify-center px-4 pb-32">
          <div className="w-full max-w-3xl">
            {/* Feature Icons */}
            {!userGoal && (
              <div className="flex items-center justify-center gap-8 mb-12">
                {[
                  { icon: Target, label: "Personalized" },
                  { icon: GraduationCap, label: "AI Practice" },
                  { icon: Zap, label: "Actionable" },
                ].map((feature, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col items-center gap-2"
                  >
                    <div className="p-4 bg-white rounded-2xl shadow-lg hover:shadow-xl transition-shadow">
                      <feature.icon className="h-6 w-6 text-gray-800" />
                    </div>
                    <span className="text-xs text-gray-600 font-medium">{feature.label}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Example prompts */}
            {!userGoal && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8">
                {EXAMPLE_INTERVIEWS.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(example.text)}
                    className="p-4 text-left bg-white border border-gray-200 rounded-xl hover:border-gray-400 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-6 h-6 rounded-lg bg-gray-100 flex items-center justify-center">
                        <span className="text-xs text-gray-700 font-semibold">→</span>
                      </div>
                      <p className="text-sm text-gray-700 font-medium">
                        {example.text}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Input Form */}
            <form
              onSubmit={handleSubmit}
              className="relative max-w-3xl mx-auto"
            >
              <div className="relative bg-white border-2 border-gray-300 rounded-2xl shadow-lg">
                <Textarea
                  placeholder="Tell me about your upcoming interview..."
                  value={userGoal}
                  onChange={(e) => {
                    setUserGoal(e.target.value)
                    // Auto-resize
                    e.target.style.height = 'auto'
                    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                      e.preventDefault()
                      handleSubmit(e)
                    }
                  }}
                  className="min-h-[52px] max-h-[200px] resize-none pr-12 py-3.5 px-4 text-base rounded-2xl border-0 focus:ring-2 focus:ring-gray-400 bg-transparent"
                  disabled={isLoading}
                  rows={1}
                />
                <Button
                  type="submit"
                  disabled={!userGoal.trim() || isLoading}
                  className="absolute right-2 bottom-2 h-8 w-8 p-0 rounded-lg bg-gray-900 hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
                  size="sm"
                >
                    {isLoading ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 16 16"
                        fill="none"
                        className="text-white"
                      >
                        <path
                          d="M.5 1.163A1 1 0 0 1 1.97.28l12.868 6.837a1 1 0 0 1 0 1.766L1.969 15.72A1 1 0 0 1 .5 14.836V10.33a1 1 0 0 1 .816-.983L8.5 8 1.316 6.653A1 1 0 0 1 .5 5.67V1.163Z"
                          fill="currentColor"
                        />
                      </svg>
                    )}
                  </Button>
              </div>
              <p className="text-xs text-gray-500 mt-3 text-center">
                Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono border border-gray-200">⌘</kbd> + <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono border border-gray-200">Enter</kbd> to submit
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
