'use client'

import { useState } from 'react'
import { X, Zap, Search, Code, BarChart3, FileText } from 'lucide-react'

interface AgentsModalProps {
  isOpen: boolean
  onClose: () => void
  onExecute: (task: string, agents: string[], strategy: string) => void
}

export default function AgentsModal({ isOpen, onClose, onExecute }: AgentsModalProps) {
  const [task, setTask] = useState('')
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [strategy, setStrategy] = useState('collaborative')
  const [isExecuting, setIsExecuting] = useState(false)

  if (!isOpen) return null

  const agents = [
    { id: 'researcher', name: 'Research Agent', icon: Search, description: 'Web research and information gathering' },
    { id: 'coder', name: 'Code Agent', icon: Code, description: 'Code generation and debugging' },
    { id: 'analyst', name: 'Analysis Agent', icon: BarChart3, description: 'Data analysis and insights' },
    { id: 'writer', name: 'Writing Agent', icon: FileText, description: 'Content creation and editing' },
  ]

  const toggleAgent = (agentId: string) => {
    setSelectedAgents(prev =>
      prev.includes(agentId)
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    )
  }

  const handleExecute = async () => {
    if (!task.trim() || selectedAgents.length === 0) return

    setIsExecuting(true)
    try {
      await onExecute(task, selectedAgents, strategy)
      onClose()
      setTask('')
      setSelectedAgents([])
    } catch (error) {
      console.error('Error executing agents:', error)
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap className="w-6 h-6 text-primary" />
            <h2 className="text-xl font-bold">Multi-Agent System</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-secondary rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Task Description</label>
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="Describe the task you want the agents to complete..."
              className="w-full p-3 border rounded-lg min-h-[100px] resize-none focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Select Agents</label>
            <div className="grid grid-cols-2 gap-2">
              {agents.map((agent) => {
                const Icon = agent.icon
                const isSelected = selectedAgents.includes(agent.id)
                return (
                  <button
                    key={agent.id}
                    onClick={() => toggleAgent(agent.id)}
                    className={`p-3 border rounded-lg text-left hover:bg-secondary transition-colors ${
                      isSelected ? 'border-primary bg-secondary' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4" />
                      <span className="font-medium">{agent.name}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{agent.description}</p>
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Execution Strategy</label>
            <div className="space-y-2">
              <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-secondary">
                <input
                  type="radio"
                  name="strategy"
                  value="collaborative"
                  checked={strategy === 'collaborative'}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">Collaborative</div>
                  <div className="text-sm text-muted-foreground">Agents work together, sharing context</div>
                </div>
              </label>
              <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-secondary">
                <input
                  type="radio"
                  name="strategy"
                  value="parallel"
                  checked={strategy === 'parallel'}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">Parallel</div>
                  <div className="text-sm text-muted-foreground">Agents work simultaneously</div>
                </div>
              </label>
              <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-secondary">
                <input
                  type="radio"
                  name="strategy"
                  value="sequential"
                  checked={strategy === 'sequential'}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">Sequential</div>
                  <div className="text-sm text-muted-foreground">Agents work one after another</div>
                </div>
              </label>
            </div>
          </div>

          <div className="flex gap-2 pt-4">
            <button
              onClick={handleExecute}
              disabled={!task.trim() || selectedAgents.length === 0 || isExecuting}
              className="flex-1 flex items-center justify-center gap-2 p-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="w-4 h-4" />
              {isExecuting ? 'Executing...' : 'Execute Task'}
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

