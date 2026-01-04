"use client"

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  getSession,
  sendMessage,
  type GetSessionResponse,
} from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Sparkles } from "lucide-react"
import ReactMarkdown from "react-markdown"
import { Checklist } from "@/components/checklist"
import { motion, AnimatePresence } from "framer-motion"

export default function SessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  const [session, setSession] = useState<GetSessionResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("Thinking...")
  const [inputValue, setInputValue] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (sessionId) {
      loadSession()
    }
  }, [sessionId])

  useEffect(() => {
    scrollToBottom()
  }, [session?.messages])
  

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const loadSession = async () => {
    try {
      setIsLoading(true)
      const data = await getSession(sessionId)
      console.log("Loaded session:", data)
      console.log("Session messages count:", data.messages?.length)
      setSession(data)
    } catch (error) {
      console.error("Failed to load session:", error)
      alert("Failed to load session")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isSending || !session) {
      return
    }

    const userMessage = inputValue.trim()
    
    // Immediately clear input and disable it
    setInputValue("")
    setIsSending(true)
    
    // Determine loading message based on context
    const messageLower = userMessage.toLowerCase()
    let initialMessage = "Thinking..."
    
    if (messageLower.includes("job description") || messageLower.includes("job posting") || messageLower.includes("jd")) {
      initialMessage = "Analyzing job description..."
    } else if (messageLower.includes("interview") && (messageLower.includes("type") || messageLower.includes("format") || messageLower.includes("style"))) {
      initialMessage = "Understanding interview format..."
    } else if (messageLower.includes("company") || messageLower.includes("role") || messageLower.includes("position")) {
      initialMessage = "Processing role details..."
    } else if (messageLower.includes("skill") || messageLower.includes("technology") || messageLower.includes("tech")) {
      initialMessage = "Analyzing required skills..."
    } else if (messageLower.includes("timeline") || messageLower.includes("when") || messageLower.includes("date")) {
      initialMessage = "Planning timeline..."
    } else if (!session.checklist) {
      initialMessage = "Creating your preparation plan..."
    } else {
      initialMessage = "Processing your message..."
    }
    
    setLoadingMessage(initialMessage)

    // Immediately add user message to chat (optimistic update)
    const tempUserMessage = { role: "user", content: userMessage }
    setSession((prevSession) => {
      if (!prevSession) return prevSession
      return {
        ...prevSession,
        messages: [...prevSession.messages, tempUserMessage],
      }
    })
    
    // Scroll to bottom to show the new message
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, 100)

    let messageInterval: NodeJS.Timeout | null = null
    try {
      // Rotate through loading messages while waiting
      const loadingMessages = [
        initialMessage,
        "Analyzing requirements...",
        "Checking job description...",
        "Creating personalized checklist..."
      ]
      
      let messageIndex = 0
      messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % loadingMessages.length
        setLoadingMessage(loadingMessages[messageIndex])
      }, 4000) // Change message every 4 seconds
      
      const response = await sendMessage(sessionId, { content: userMessage })
      if (messageInterval) clearInterval(messageInterval)
      // Update session with new messages and checklist - ensure we use the full array from response
      if (response.messages && Array.isArray(response.messages)) {
        setSession((prevSession) => {
          if (!prevSession) return prevSession
          return {
            ...prevSession,
            messages: response.messages,
            checklist: response.checklist || prevSession.checklist, // Update checklist if provided
          }
        })
      }
    } catch (error) {
      if (messageInterval) clearInterval(messageInterval)
      console.error("Failed to send message:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to send message. Please try again."
      console.error("Error details:", errorMessage)
      alert(`Failed to send message: ${errorMessage}`)
      // Remove the optimistic message on error
      setSession((prevSession) => {
        if (!prevSession) return prevSession
        return {
          ...prevSession,
          messages: prevSession.messages.slice(0, -1),
        }
      })
    } finally {
      if (messageInterval) clearInterval(messageInterval)
      setIsSending(false)
      setLoadingMessage("Thinking...") // Reset loading message
      // Auto-resize textarea and focus it
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
        textareaRef.current.focus()
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleSend(e)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center ml-0 lg:ml-64">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center ml-0 lg:ml-64">
        <p className="text-gray-500">Session not found</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-white ml-0 lg:ml-64">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-4 py-3">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-[#171717]" />
            <h2 className="text-lg font-semibold text-[#171717]">{session.title}</h2>
          </div>
        </div>
      </div>

      {/* Main Content: Checklist (if available) or Messages */}
      {session.checklist ? (
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-4xl mx-auto">
            <Checklist 
              checklist={session.checklist} 
              sessionId={sessionId}
              onUpdate={(updatedChecklist) => {
                setSession((prev) => {
                  if (!prev) return prev
                  return {
                    ...prev,
                    checklist: updatedChecklist,
                  }
                })
              }}
            />
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <AnimatePresence>
            {session.messages && session.messages.length > 0 ? (
              session.messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  className={`flex gap-4 ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.05 }}
                >
                  {msg.role === "assistant" && (
                    <motion.div
                      className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-100 to-slate-100 flex items-center justify-center shadow-sm"
                      whileHover={{ scale: 1.1, rotate: 5 }}
                    >
                      <Sparkles className="h-4 w-4 text-blue-600" />
                    </motion.div>
                  )}
                  <motion.div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                      msg.role === "user"
                                ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg"
                        : "bg-white border border-gray-200 text-gray-900 shadow-sm"
                    }`}
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown
                          components={{
                            ul: ({ children }) => (
                              <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>
                            ),
                            li: ({ children }) => <li className="ml-2">{children}</li>,
                            p: ({ children }) => <p className="my-2">{children}</p>,
                            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                            code: ({ children }) => (
                              <code className="bg-gray-200 px-1.5 py-0.5 rounded text-sm font-mono">
                                {children}
                              </code>
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </motion.div>
                  {msg.role === "user" && (
                    <motion.div
                      className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-blue-700 flex items-center justify-center shadow-lg"
                      whileHover={{ scale: 1.1 }}
                    >
                      <span className="text-white text-sm font-medium">U</span>
                    </motion.div>
                  )}
                </motion.div>
              ))
            ) : (
              <motion.div
                className="text-center text-gray-500 py-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                No messages yet. Start the conversation!
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {isSending && (
              <motion.div
                className="flex gap-4 justify-start"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <motion.div
                  className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-100 to-slate-100 flex items-center justify-center"
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="h-4 w-4 text-blue-600" />
                </motion.div>
                <motion.div
                  className="bg-gray-100 rounded-2xl px-4 py-3"
                  initial={{ scale: 0.9 }}
                  animate={{ scale: 1 }}
                >
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      {[0, 150, 300].map((delay, i) => (
                        <motion.span
                          key={i}
                          className="w-2 h-2 bg-gray-400 rounded-full"
                          animate={{ y: [0, -8, 0] }}
                          transition={{
                            duration: 0.6,
                            repeat: Infinity,
                            delay: delay / 1000,
                            ease: "easeInOut",
                          }}
                        />
                      ))}
                    </div>
                    <motion.span
                      className="text-gray-600 text-sm ml-2"
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      {loadingMessage}
                    </motion.span>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </div>
      )}

      {/* Input - Only show if no checklist (still gathering info) */}
      {!session.checklist && (
        <div className="flex-shrink-0 border-t border-gray-200 bg-white px-4 py-4">
          <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSend} className="relative">
            <div className="relative bg-white border border-gray-300 rounded-2xl shadow-lg hover:shadow-xl transition-shadow">
              <Textarea
                ref={textareaRef}
                placeholder="Type your message..."
                value={inputValue}
                onChange={(e) => {
                  setInputValue(e.target.value)
                  // Auto-resize
                  e.target.style.height = "auto"
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
                }}
                onKeyDown={handleKeyDown}
                className="min-h-[52px] max-h-[200px] resize-none pr-12 py-3.5 px-4 text-base rounded-2xl border-0 focus:ring-0 bg-transparent"
                disabled={isSending}
                rows={1}
              />
              <Button
                type="submit"
                disabled={!inputValue.trim() || isSending}
                className="absolute right-2 bottom-2 h-8 w-8 p-0 rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
                size="sm"
              >
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
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono">⌘</kbd> + <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono">Enter</kbd> to send
            </p>
          </form>
        </div>
      </div>
      )}
    </div>
  )
}
