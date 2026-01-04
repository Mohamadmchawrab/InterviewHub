"use client"

import { useState, useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Plus, MessageSquare, ChevronLeft, Sparkles, Trash2 } from "lucide-react"
import { listSessions, deleteSession, type SessionListItem } from "@/lib/api"
import { motion } from "framer-motion"

export function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isOpen, setIsOpen] = useState(true)

  // Refresh sessions when pathname changes (new session created)
  useEffect(() => {
    loadSessions()
  }, [pathname])

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      const data = await listSessions()
      setSessions(data)
    } catch (error) {
      console.error("Failed to load sessions:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = () => {
    router.push("/")
  }

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation() // Prevent navigation when clicking delete
    
    if (!confirm("Are you sure you want to delete this chat?")) {
      return
    }

    try {
      await deleteSession(sessionId)
      // Remove from local state
      setSessions(sessions.filter(s => s.session_id !== sessionId))
      
      // If we're on the deleted session's page, redirect to home
      if (pathname === `/session/${sessionId}`) {
        router.push("/")
      }
    } catch (error) {
      console.error("Failed to delete session:", error)
      alert("Failed to delete session. Please try again.")
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return "Today"
    } else if (diffDays === 1) {
      return "Yesterday"
    } else if (diffDays < 7) {
      return `${diffDays} days ago`
    } else {
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
    }
  }

  const isActive = (sessionId: string) => {
    return pathname === `/session/${sessionId}`
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed left-0 top-0 bottom-0 w-12 bg-gray-50 border-r border-gray-200 hover:bg-gray-100 transition-colors z-40 hidden lg:block"
        aria-label="Open sidebar"
      >
        <div className="flex items-center justify-center h-full">
          <MessageSquare className="h-5 w-5 text-gray-600" />
        </div>
      </button>
    )
  }

  return (
    <div className="fixed left-0 top-0 bottom-0 w-64 bg-gray-50 border-r border-gray-200 flex flex-col z-40 hidden lg:flex">
      {/* Header with Logo */}
      <div className="p-4 border-b border-gray-200">
        {/* Logo */}
        <motion.div
          className="flex items-center gap-2 mb-4"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="relative">
            <Sparkles className="h-6 w-6 text-blue-600" />
            <motion.div
              className="absolute inset-0 h-6 w-6 bg-blue-200 rounded-full blur-md opacity-50"
              animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>
          <h1 className="text-lg font-bold bg-gradient-to-r from-blue-600 via-blue-700 to-slate-700 bg-clip-text text-transparent">
            InterviewHub
          </h1>
        </motion.div>
        
        {/* New Chat Button */}
        <Button
          onClick={handleNewChat}
          className="w-full justify-start gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white border-0 rounded-xl shadow-md hover:shadow-lg transition-all duration-300"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-sm text-gray-500">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">
            No previous chats
          </div>
        ) : (
          <div className="p-2">
            {sessions.map((session) => (
              <motion.div
                key={session.session_id}
                className={`relative group rounded-xl mb-1 transition-all ${
                  isActive(session.session_id)
                    ? "bg-gray-200"
                    : "hover:bg-gray-100"
                }`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
              >
                <button
                  onClick={() => {
                    router.push(`/session/${session.session_id}`)
                  }}
                  className={`w-full text-left p-3 rounded-xl transition-colors ${
                    isActive(session.session_id)
                      ? "text-gray-900"
                      : "text-gray-700"
                  }`}
                >
                  <div className="flex items-start gap-2 pr-8">
                    <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 text-gray-500" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {session.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {formatDate(session.created_at)}
                      </p>
                    </div>
                  </div>
                </button>
                {/* Delete Button */}
                <motion.button
                  onClick={(e) => handleDeleteSession(e, session.session_id)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-100 text-red-600 transition-all duration-200"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label="Delete chat"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </motion.button>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200">
        <button
          onClick={() => setIsOpen(false)}
          className="w-full flex items-center gap-2 p-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
          Collapse
        </button>
      </div>
    </div>
  )
}

