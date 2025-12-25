'use client'

import { useState } from 'react'
import { MessageSquare, Plus, ChevronLeft, ChevronRight, Settings, Zap, Trash2, X } from 'lucide-react'

interface SidebarProps {
  open: boolean
  onToggle: () => void
  conversations: any[]
  currentConversation: number | null
  onSelectConversation: (id: number | null) => void
  onNewConversation: () => void
  onAgentsClick: () => void
  onSettingsClick: () => void
  onDeleteConversation?: (id: number) => void
}

export default function Sidebar({
  open,
  onToggle,
  conversations,
  currentConversation,
  onSelectConversation,
  onNewConversation,
  onAgentsClick,
  onSettingsClick,
  onDeleteConversation
}: SidebarProps) {
  const [hoveredConv, setHoveredConv] = useState<number | null>(null)

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation() // Prevent selecting the conversation when clicking delete
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      if (onDeleteConversation) {
        onDeleteConversation(id)
      }
    }
  }
  return (
    <div className="w-64 md:w-80 bg-secondary border-r border-border/50 h-full grid grid-rows-[auto_auto_1fr_auto]">
      {/* Header - Row 1 */}
      <div className="p-3 sm:p-4 border-b border-border/50 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Conversations</h2>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg hover:bg-accent transition-colors md:hidden"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* New Conversation Button - Row 2 */}
      <div className="p-3 sm:p-4 border-b border-border/50">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center gap-2 p-2.5 sm:p-3 bg-gradient-to-r from-primary to-purple-600 text-primary-foreground rounded-xl hover:opacity-90 transition-all duration-300 hover:scale-105 shadow-lg"
        >
          <Plus className="w-4 h-4" />
          <span className="text-sm font-medium">New Chat</span>
        </button>
      </div>

      {/* Conversations List - Row 3 (takes remaining space) */}
      <div className="overflow-y-auto p-2 sm:p-3 min-h-0">
        {conversations.length === 0 ? (
          <div className="text-center text-sm text-muted-foreground py-8">
            <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
            No conversations yet
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onMouseEnter={() => setHoveredConv(conv.id)}
                onMouseLeave={() => setHoveredConv(null)}
                className="relative group"
              >
                <button
                  onClick={() => onSelectConversation(conv.id)}
                  className={`w-full text-left p-2.5 sm:p-3 rounded-xl hover:bg-accent transition-all duration-200 ${
                    currentConversation === conv.id
                      ? 'bg-gradient-to-r from-accent to-accent/80 shadow-md'
                      : 'hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-center gap-2 pr-8">
                    <MessageSquare className="w-4 h-4 flex-shrink-0 text-muted-foreground" />
                    <span className="text-sm truncate flex-1 text-left">
                      {conv.title || 'New Chat'}
                    </span>
                  </div>
                </button>
                {onDeleteConversation && (
                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    className={`absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-red-500 hover:text-white transition-all duration-200 ${
                      hoveredConv === conv.id ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
                    } group-hover:opacity-100 group-hover:scale-100`}
                    title="Delete conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Actions - Row 4 (always at bottom) */}
      <div className="p-3 sm:p-4 border-t border-border/50 space-y-1">
        <button
          onClick={onAgentsClick}
          className="w-full flex items-center justify-start gap-3 p-2.5 sm:p-3 rounded-xl hover:bg-accent transition-all duration-200 hover:shadow-sm"
        >
          <Zap className="w-4 h-4 text-primary flex-shrink-0" />
          <span className="text-sm font-medium text-left">AI Agents</span>
        </button>
        <button
          onClick={onSettingsClick}
          className="w-full flex items-center justify-start gap-3 p-2.5 sm:p-3 rounded-xl hover:bg-accent transition-all duration-200 hover:shadow-sm"
        >
          <Settings className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          <span className="text-sm font-medium text-left">Settings</span>
        </button>
      </div>
    </div>
  )
}

