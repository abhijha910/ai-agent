'use client'

import { useState, useEffect } from 'react'
import ChatInterface from '@/components/ChatInterface'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import SettingsModal from '@/components/SettingsModal'
import AgentsModal from '@/components/AgentsModal'

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true) // Start open on desktop
  const [conversations, setConversations] = useState<any[]>([])
  const [currentConversation, setCurrentConversation] = useState<number | null>(null)
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [agentsOpen, setAgentsOpen] = useState(false)

  // Load conversations on mount and when new conversation is created
  useEffect(() => {
    fetchConversations()
  }, [])

  // Refresh conversations periodically (reduced frequency)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchConversations()
    }, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [])

  // Use environment variable for API URL with fallback
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const fetchConversations = async () => {
    try {
      const response = await fetch(`${API_URL}/api/chat/conversations`)
      if (response.ok) {
        const data = await response.json()
        setConversations(data.conversations || [])
      }
    } catch (error) {
      console.error('Error fetching conversations:', error)
    }
  }

  const handleSelectConversation = (id: number | null) => {
    setCurrentConversation(id)
    // Messages will be loaded by ChatInterface
  }

  const handleNewConversation = async () => {
    // Create new conversation in database
    try {
      const response = await fetch(`${API_URL}/api/chat/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: null })
      })
      if (response.ok) {
        const data = await response.json()
        setCurrentConversation(data.id)
        // Refresh conversations list
        fetchConversations()
      } else {
        // Fallback: use timestamp as ID
        setCurrentConversation(Date.now())
      }
    } catch (error) {
      console.error('Error creating conversation:', error)
      // Fallback: use timestamp as ID
      setCurrentConversation(Date.now())
    }
  }

  const handleExecuteAgents = async (task: string, agents: string[], strategy: string) => {
    try {
      const response = await fetch(`${API_URL}/api/agents/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, agents, strategy })
      })
      const data = await response.json()
      // You can display the result in the chat or a notification
      console.log('Agent execution result:', data)
    } catch (error) {
      console.error('Error executing agents:', error)
    }
  }

  const handleDeleteConversation = async (id: number) => {
    try {
      const response = await fetch(`${API_URL}/api/chat/conversations/${id}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        // If deleted conversation was current, clear it
        if (currentConversation === id) {
          setCurrentConversation(null)
        }
        // Refresh conversations list
        fetchConversations()
      } else {
        alert('Failed to delete conversation')
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
      alert('Error deleting conversation. Please try again.')
    }
  }

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex h-screen">
        {/* Sidebar */}
        <div className={`
          fixed md:relative z-50 h-full transition-all duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0 w-64 md:w-80' : '-translate-x-full w-0 md:w-0 md:translate-x-0'}
          ${sidebarOpen ? 'md:translate-x-0' : ''}
        `}>
          <Sidebar
            open={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            conversations={conversations}
            currentConversation={currentConversation}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            onAgentsClick={() => setAgentsOpen(true)}
            onSettingsClick={() => setSettingsOpen(true)}
            onDeleteConversation={handleDeleteConversation}
          />
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0 relative max-w-full overflow-hidden">
          <Header
            model={selectedModel}
            onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          />
          <div className="flex-1 min-h-0 overflow-hidden">
            <div className="h-full max-w-full overflow-hidden">
              <ChatInterface
                conversationId={currentConversation}
                model={selectedModel}
                onNewConversation={handleNewConversation}
                onConversationCreated={(id) => {
                  setCurrentConversation(id)
                  fetchConversations()
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        currentModel={selectedModel}
        onModelChange={setSelectedModel}
      />

      <AgentsModal
        isOpen={agentsOpen}
        onClose={() => setAgentsOpen(false)}
        onExecute={handleExecuteAgents}
      />
    </div>
  )
}
