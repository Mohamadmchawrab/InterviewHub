"use client"

import { useState } from "react"
import { ChecklistStructure, TodoItem, updateTodo } from "@/lib/api"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle2, Circle, Clock, AlertCircle, GraduationCap } from "lucide-react"
import { InterviewModal } from "@/components/interview-modal"

interface ChecklistProps {
  checklist: ChecklistStructure
  sessionId: string
  onUpdate?: (updatedChecklist: ChecklistStructure) => void
}

export function Checklist({ checklist: initialChecklist, sessionId, onUpdate }: ChecklistProps) {
  const [checklist, setChecklist] = useState<ChecklistStructure>(initialChecklist)
  const [updatingIds, setUpdatingIds] = useState<Set<string>>(new Set())
  const [interviewTodoId, setInterviewTodoId] = useState<string | null>(null)
  const [interviewTodoText, setInterviewTodoText] = useState<string | null>(null)

  const handleToggleTodo = async (item: TodoItem) => {
    const newStatus = item.status === "done" ? "todo" : "done"
    setUpdatingIds((prev) => new Set(prev).add(item.id))

    try {
      await updateTodo(sessionId, item.id, { status: newStatus })
      
      // Update local state
      const updatedChecklist = { ...checklist }
      updatedChecklist.groups = checklist.groups.map((group) => ({
        ...group,
        items: group.items.map((i) =>
          i.id === item.id ? { ...i, status: newStatus as "todo" | "done" } : i
        ),
      }))
      
      setChecklist(updatedChecklist)
      if (onUpdate) {
        onUpdate(updatedChecklist)
      }
    } catch (error) {
      console.error("Failed to update todo:", error)
      alert("Failed to update todo. Please try again.")
    } finally {
      setUpdatingIds((prev) => {
        const next = new Set(prev)
        next.delete(item.id)
        return next
      })
    }
  }

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case "high":
        return "bg-red-100 text-red-800 border-red-300"
      case "med":
        return "bg-yellow-100 text-yellow-800 border-yellow-300"
      case "low":
        return "bg-blue-100 text-blue-800 border-blue-300"
      default:
        return "bg-gray-100 text-gray-800 border-gray-300"
    }
  }

  const totalItems = checklist.groups.reduce((sum, group) => sum + group.items.length, 0)
  const completedItems = checklist.groups.reduce(
    (sum, group) => sum + group.items.filter((item) => item.status === "done").length,
    0
  )

  const completionPercentage = totalItems > 0 ? (completedItems / totalItems) * 100 : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold text-[#171717] mb-2">{checklist.title}</h2>
        <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
          <span>
            {completedItems} of {totalItems} completed
          </span>
          {/* Progress Bar */}
          <div className="flex-1 max-w-xs">
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div 
                className="h-2 bg-gradient-to-r from-blue-500 via-blue-600 to-slate-600 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>
          </div>
          <span className="text-xs font-medium text-blue-600">
            {Math.round(completionPercentage)}%
          </span>
          {checklist.next_3_actions && checklist.next_3_actions.length > 0 && (
            <span className="flex items-center gap-1">
              <AlertCircle className="h-4 w-4" />
              {checklist.next_3_actions.length} priority actions
            </span>
          )}
        </div>
      </div>

      {/* Next 3 Actions */}
      {checklist.next_3_actions && checklist.next_3_actions.length > 0 && (
        <Card className="p-4 bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            Next 3 Priority Actions
          </h3>
          <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
            {checklist.next_3_actions.map((action, idx) => (
              <li key={idx}>{action}</li>
            ))}
          </ol>
        </Card>
      )}

      {/* Assumptions */}
      {checklist.assumptions && checklist.assumptions.length > 0 && (
        <Card className="p-4 bg-yellow-50 border-yellow-200">
          <h3 className="font-semibold text-yellow-900 mb-2">Assumptions</h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
            {checklist.assumptions.map((assumption, idx) => (
              <li key={idx}>{assumption}</li>
            ))}
          </ul>
        </Card>
      )}

      {/* Checklist Groups */}
      <div className="space-y-6">
        {checklist.groups.map((group) => {
          if (group.items.length === 0) return null

          return (
            <Card key={group.key} className="p-5">
              <h3 className="font-semibold text-lg text-[#171717] mb-4">{group.label}</h3>
              <div className="space-y-3">
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border ${
                      item.status === "done"
                        ? "bg-green-50 border-green-200"
                        : "bg-white border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <button
                      onClick={() => handleToggleTodo(item)}
                      disabled={updatingIds.has(item.id)}
                      className="flex-shrink-0 mt-0.5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-opacity hover:opacity-80"
                      aria-label={item.status === "done" ? "Mark as incomplete" : "Mark as complete"}
                    >
                      {item.status === "done" ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      ) : (
                        <Circle className="h-5 w-5 text-gray-400" />
                      )}
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p
                          className={`text-sm ${
                            item.status === "done" ? "line-through text-gray-500" : "text-gray-900"
                          }`}
                        >
                          {item.text}
                        </p>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {item.priority && (
                            <Badge className={getPriorityColor(item.priority)} variant="outline">
                              {item.priority}
                            </Badge>
                          )}
                          {item.estimate_minutes && (
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <Clock className="h-3 w-3" />
                              {item.estimate_minutes}m
                            </div>
                          )}
                        </div>
                      </div>
                      {item.rationale && (
                        <p className="text-xs text-gray-500 mt-1 ml-7">{item.rationale}</p>
                      )}
                      {/* Test Knowledge button for Skills items */}
                      {group.key === "skills" && item.status !== "done" && (
                        <div className="mt-2 ml-7">
                          <Button
                            onClick={() => {
                              // Validate item.id is a proper UUID before starting interview
                              const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
                              if (!uuidRegex.test(item.id)) {
                                console.error("Invalid todo ID format:", item.id)
                                alert("Invalid checklist item ID. Please refresh the page to regenerate the checklist.")
                                return
                              }
                              setInterviewTodoId(item.id)
                              setInterviewTodoText(item.text)
                            }}
                            variant="outline"
                            size="sm"
                            className="text-xs"
                          >
                            <GraduationCap className="h-3 w-3 mr-1" />
                            Test Knowledge
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )
        })}
      </div>

      {/* Interview Modal */}
      {interviewTodoId && interviewTodoText && (
        <InterviewModal
          open={!!interviewTodoId}
          onClose={() => {
            setInterviewTodoId(null)
            setInterviewTodoText(null)
          }}
          sessionId={sessionId}
          todoId={interviewTodoId}
          todoText={interviewTodoText}
          onComplete={async (passed, rating) => {
            // Auto-mark as done if passed
            if (passed && interviewTodoId) {
              // Use a small delay to ensure the modal state has updated
              setTimeout(() => {
                const item = checklist.groups
                  .flatMap((g) => g.items)
                  .find((i) => i.id === interviewTodoId)
                
                if (item && item.status !== "done") {
                  handleToggleTodo(item)
                }
              }, 200)
            }
          }}
        />
      )}
    </div>
  )
}

