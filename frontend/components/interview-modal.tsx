"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { startInterview, answerInterviewQuestion, type InterviewResponse, type InterviewQuestion } from "@/lib/api"
import { CheckCircle2, XCircle, Loader2, Sparkles } from "lucide-react"

interface InterviewModalProps {
  open: boolean
  onClose: () => void
  sessionId: string
  todoId: string
  todoText: string
  onComplete?: (passed: boolean, rating: number) => void
}

export function InterviewModal({
  open,
  onClose,
  sessionId,
  todoId,
  todoText,
  onComplete,
}: InterviewModalProps) {
  const [currentQuestion, setCurrentQuestion] = useState<InterviewQuestion | null>(null)
  const [answer, setAnswer] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [history, setHistory] = useState<Array<{ role: "user" | "assistant"; content: string }>>([])
  const [isComplete, setIsComplete] = useState(false)
  const [rating, setRating] = useState<number | null>(null)
  const [passed, setPassed] = useState<boolean | null>(null)
  const [overallFeedback, setOverallFeedback] = useState<string | null>(null)

  const handleStart = async () => {
    // Validate todoId is a proper UUID before starting
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (!uuidRegex.test(todoId)) {
      alert("Invalid checklist item ID detected. Please refresh the page to regenerate the checklist with proper IDs, then try again.")
      onClose()
      return
    }
    
    setIsLoading(true)
    try {
      const response = await startInterview(sessionId, todoId, todoText)
      if (response.question) {
        setCurrentQuestion(response.question)
        setHistory([{ role: "assistant", content: response.question.question }])
      }
    } catch (error) {
      console.error("Failed to start interview:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to start interview. Please try again."
      if (errorMessage.includes("Invalid todo_id")) {
        alert("Invalid checklist item ID. Please refresh the page to regenerate the checklist, then try again.")
      } else {
        alert(errorMessage)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) return

    setIsLoading(true)
    const userAnswer = answer
    setAnswer("")
    setHistory((prev) => [...prev, { role: "user", content: userAnswer }])

    try {
      const response = await answerInterviewQuestion(sessionId, todoId, userAnswer)

      if (response.is_complete) {
        // Interview complete
        setIsComplete(true)
        setRating(response.rating || null)
        setPassed(response.passed || null)
        setOverallFeedback(response.overall_feedback || null)
        // Auto-call onComplete if passed (don't wait for button click)
        if (onComplete && response.passed !== undefined && response.rating !== undefined && response.passed) {
          onComplete(response.passed, response.rating)
        }
      } else {
        // Show feedback if available
        if (response.feedback) {
          setFeedback(response.feedback)
          setHistory((prev) => [...prev, { role: "assistant", content: `Feedback: ${response.feedback}` }])
        }

        // Show next question
        if (response.question) {
          setCurrentQuestion(response.question)
          setHistory((prev) => [...prev, { role: "assistant", content: response.question!.question }])
          setFeedback(null) // Clear feedback for next question
        }
      }
    } catch (error) {
      console.error("Failed to answer question:", error)
      alert("Failed to submit answer. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    if (isComplete) {
      // Reset state when closing after completion
      setCurrentQuestion(null)
      setAnswer("")
      setFeedback(null)
      setHistory([])
      setIsComplete(false)
      setRating(null)
      setPassed(null)
      setOverallFeedback(null)
    }
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Knowledge Test: {todoText}
          </DialogTitle>
          <DialogDescription>
            Test your understanding of this skill. Answer 3-5 questions to get rated and receive feedback.
          </DialogDescription>
        </DialogHeader>

        {!currentQuestion && !isComplete && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Ready to test your knowledge? Click the button below to start the interview.
            </p>
            <Button onClick={handleStart} disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Starting...
                </>
              ) : (
                "Start Knowledge Test"
              )}
            </Button>
          </div>
        )}

        {currentQuestion && !isComplete && (
          <div className="space-y-4">
            {/* Progress */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                Question {currentQuestion.question_number} of {currentQuestion.total_questions}
              </span>
              <div className="flex gap-1">
                {Array.from({ length: currentQuestion.total_questions }).map((_, i) => (
                  <div
                    key={i}
                    className={`h-2 w-8 rounded ${
                      i < currentQuestion.question_number
                        ? "bg-green-500"
                        : i === currentQuestion.question_number - 1
                        ? "bg-blue-500"
                        : "bg-gray-200"
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Question */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="font-semibold text-blue-900 mb-2">Question:</p>
              <p className="text-blue-800">
                {typeof currentQuestion.question === 'string' 
                  ? currentQuestion.question 
                  : JSON.stringify(currentQuestion.question)}
              </p>
            </div>

            {/* Feedback from previous answer */}
            {feedback && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="font-semibold text-yellow-900 mb-1">Feedback:</p>
                <p className="text-yellow-800 text-sm">{feedback}</p>
              </div>
            )}

            {/* Answer input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Your Answer:</label>
              <Textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type your answer here..."
                className="min-h-[120px]"
                disabled={isLoading}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault()
                    handleSubmitAnswer()
                  }
                }}
              />
            </div>

            <Button
              onClick={handleSubmitAnswer}
              disabled={!answer.trim() || isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Submit Answer"
              )}
            </Button>

            <p className="text-xs text-gray-500 text-center">
              Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">⌘</kbd> +{" "}
              <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">Enter</kbd> to submit
            </p>
          </div>
        )}

        {isComplete && (
          <div className="space-y-4">
            {/* Results */}
            <div className="text-center space-y-2">
              {passed ? (
                <div className="flex items-center justify-center gap-2 text-green-600">
                  <CheckCircle2 className="h-8 w-8" />
                  <span className="text-xl font-semibold">You Passed!</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2 text-orange-600">
                  <XCircle className="h-8 w-8" />
                  <span className="text-xl font-semibold">Keep Practicing</span>
                </div>
              )}

              {rating !== null && (
                <div className="flex items-center justify-center gap-2">
                  <span className="text-2xl font-bold">{rating.toFixed(1)}</span>
                  <span className="text-gray-600">/ 10</span>
                </div>
              )}
            </div>

            {/* Overall Feedback */}
            {overallFeedback && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="font-semibold text-gray-900 mb-2">Overall Assessment:</p>
                <p className="text-gray-700 text-sm whitespace-pre-wrap">{overallFeedback}</p>
              </div>
            )}

            <div className="flex gap-2">
              <Button onClick={handleClose} className="flex-1">
                Close
              </Button>
              {/* Note: onComplete is already called automatically when interview passes */}
              {/* This button just closes the modal */}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

