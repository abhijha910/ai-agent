'use client'

import { useState, useRef, useEffect } from 'react'
import { Settings, Trash2, Download, Upload, HelpCircle } from 'lucide-react'

interface MenuDropdownProps {
  isOpen: boolean
  onClose: () => void
  onSettingsClick: () => void
  onClearChat: () => void
  onExportChat: () => void
  onImportChat: () => void
}

export default function MenuDropdown({ 
  isOpen, 
  onClose, 
  onSettingsClick, 
  onClearChat,
  onExportChat,
  onImportChat
}: MenuDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      ref={dropdownRef}
      className="absolute right-4 top-16 bg-background border rounded-lg shadow-lg p-2 min-w-[200px] z-50"
    >
      <button
        onClick={() => {
          onSettingsClick()
          onClose()
        }}
        className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-secondary transition-colors"
      >
        <Settings className="w-4 h-4" />
        <span>Settings</span>
      </button>
      <button
        onClick={() => {
          onExportChat()
          onClose()
        }}
        className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-secondary transition-colors"
      >
        <Download className="w-4 h-4" />
        <span>Export Chat</span>
      </button>
      <button
        onClick={() => {
          onImportChat()
          onClose()
        }}
        className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-secondary transition-colors"
      >
        <Upload className="w-4 h-4" />
        <span>Import Chat</span>
      </button>
      <button
        onClick={() => {
          onClearChat()
          onClose()
        }}
        className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-secondary transition-colors text-red-500"
      >
        <Trash2 className="w-4 h-4" />
        <span>Clear Chat</span>
      </button>
      <div className="border-t my-1"></div>
      <button
        onClick={() => {
          window.open('https://github.com', '_blank')
          onClose()
        }}
        className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-secondary transition-colors"
      >
        <HelpCircle className="w-4 h-4" />
        <span>Help & Docs</span>
      </button>
    </div>
  )
}

