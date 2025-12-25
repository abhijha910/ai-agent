'use client'

import { useState } from 'react'
import { X, Save } from 'lucide-react'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  currentModel: string
  onModelChange: (model: string) => void
}

export default function SettingsModal({ isOpen, onClose, currentModel, onModelChange }: SettingsModalProps) {
  const [selectedModel, setSelectedModel] = useState(currentModel)

  if (!isOpen) return null

  const models = [
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', description: 'Google - Fast and efficient' },
    { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', description: 'Google - More powerful' },
    { id: 'gemini-flash-latest', name: 'Gemini Flash Latest', description: 'Google - Latest flash model' },
    { id: 'gpt-4', name: 'GPT-4', description: 'OpenAI (requires API key)' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'OpenAI (requires API key)' },
    { id: 'claude-3-opus', name: 'Claude 3 Opus', description: 'Anthropic (requires API key)' },
  ]

  const handleSave = () => {
    onModelChange(selectedModel)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Settings</h2>
          <button onClick={onClose} className="p-2 hover:bg-secondary rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">AI Model</label>
            <div className="space-y-2">
              {models.map((model) => (
                <label
                  key={model.id}
                  className={`flex items-center p-3 border rounded-lg cursor-pointer hover:bg-secondary ${
                    selectedModel === model.id ? 'border-primary bg-secondary' : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="model"
                    value={model.id}
                    checked={selectedModel === model.id}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-medium">{model.name}</div>
                    <div className="text-sm text-muted-foreground">{model.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="flex gap-2 pt-4">
            <button
              onClick={handleSave}
              className="flex-1 flex items-center justify-center gap-2 p-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90"
            >
              <Save className="w-4 h-4" />
              Save Settings
            </button>
            <button
              onClick={onClose}
              className="px-4 p-2 border rounded-lg hover:bg-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

