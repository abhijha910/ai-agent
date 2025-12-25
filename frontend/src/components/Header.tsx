'use client'

import { useState } from 'react'
import { Sparkles, Menu } from 'lucide-react'
import MenuDropdown from './MenuDropdown'

interface HeaderProps {
  model: string
  onMenuClick: () => void
}

export default function Header({ model, onMenuClick }: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false)

  const getModelDisplayName = (modelName: string) => {
    const modelMap: { [key: string]: string } = {
      'gemini-2.5-flash': 'Gemini 2.5 Flash',
      'gemini-2.5-pro': 'Gemini 2.5 Pro',
      'gemini-flash-latest': 'Gemini Flash Latest',
      'gpt-4': 'GPT-4',
      'gpt-3.5-turbo': 'GPT-3.5 Turbo',
      'claude-3-opus': 'Claude 3 Opus',
    }
    return modelMap[modelName] || modelName
  }

  return (
    <header className="border-b border-border/50 p-3 sm:p-4 flex items-center justify-between relative bg-background/80 backdrop-blur-sm">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <button
          onClick={onMenuClick}
          className="p-1.5 rounded-lg hover:bg-accent transition-colors md:hidden"
          aria-label="Toggle sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
        <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-primary flex-shrink-0" />
        <h1 className="text-lg sm:text-xl font-bold truncate">Advanced AI Agent</h1>
      </div>
      <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
        <span className="text-xs sm:text-sm text-muted-foreground hidden sm:inline truncate max-w-[120px] md:max-w-none">
          {getModelDisplayName(model)}
        </span>
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-2 rounded-lg hover:bg-accent transition-colors"
            aria-label="Menu"
          >
            <Menu className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>
          <MenuDropdown
            isOpen={menuOpen}
            onClose={() => setMenuOpen(false)}
            onSettingsClick={onMenuClick}
            onClearChat={() => {
              if (confirm('Are you sure you want to clear this chat?')) {
                window.location.reload()
              }
            }}
            onExportChat={() => {
              const chatData = JSON.stringify({ messages: [] }, null, 2)
              const blob = new Blob([chatData], { type: 'application/json' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `chat-${Date.now()}.json`
              a.click()
            }}
            onImportChat={() => {
              const input = document.createElement('input')
              input.type = 'file'
              input.accept = '.json'
              input.onchange = (e) => {
                const file = (e.target as HTMLInputElement).files?.[0]
                if (file) {
                  const reader = new FileReader()
                  reader.onload = (event) => {
                    try {
                      const data = JSON.parse(event.target?.result as string)
                      console.log('Imported chat:', data)
                      alert('Chat imported successfully!')
                    } catch (error) {
                      alert('Error importing chat file')
                    }
                  }
                  reader.readAsText(file)
                }
              }
              input.click()
            }}
          />
        </div>
      </div>
    </header>
  )
}

