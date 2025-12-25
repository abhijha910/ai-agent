'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Sparkles, Mic, MicOff, Paperclip, X, Image as ImageIcon, Volume2, Wand2, Edit3, Check, X as XIcon } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Attachment {
  id: string
  type: 'image' | 'file'
  name: string
  url: string
  file?: File
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  attachments?: Attachment[]
}

interface ChatInterfaceProps {
  conversationId: number | null
  model?: string
  onNewConversation?: () => void
  onConversationCreated?: (id: number) => void
}

export default function ChatInterface({ conversationId, model = 'gpt-3.5-turbo', onNewConversation, onConversationCreated }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [wsConnected, setWsConnected] = useState(false)
  const [playingAudio, setPlayingAudio] = useState<string | null>(null)
  const [voiceMode, setVoiceMode] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [continuousListening, setContinuousListening] = useState(false)
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editedContent, setEditedContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const currentMessageRef = useRef<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const recognitionRef = useRef<any>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Connect to WebSocket with retry logic
    let reconnectAttempts = 0
    const maxReconnectAttempts = 5
    const reconnectDelay = 2000
    let isConnecting = false
    let shouldReconnect = true

    const connectWebSocket = () => {
      // Prevent multiple connection attempts
      if (isConnecting || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
        return
      }

      // Don't reconnect if we're cleaning up
      if (!shouldReconnect) {
        return
      }

      isConnecting = true

      // Close existing connection if any
      if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
        wsRef.current.close()
        wsRef.current = null
      }

      try {
        // Use environment variable for WebSocket URL with fallback
        const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
        const websocket = new WebSocket(WS_URL)
        wsRef.current = websocket

        websocket.onopen = () => {
          console.log('WebSocket connected')
          setWsConnected(true)
          setWs(websocket)
          reconnectAttempts = 0
          isConnecting = false
        }
        
        websocket.onmessage = (event) => {
          const data = JSON.parse(event.data)
          
          if (data.type === 'chunk') {
            // Clear loading immediately when first chunk arrives
            setIsLoading(false)
            currentMessageRef.current += data.content
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1]
              if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id === 'streaming') {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMessage, content: currentMessageRef.current }
                ]
              } else {
                const newMessage: Message = {
                  id: 'streaming',
                  role: 'assistant',
                  content: currentMessageRef.current,
                  timestamp: new Date()
                }
                return [...prev, newMessage]
              }
            })
          } else if (data.type === 'complete') {
            // CRITICAL: Clear loading state immediately - do this FIRST
            setIsLoading(false)
            // Update the streaming message ID to a permanent one
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1]
              if (lastMessage && lastMessage.id === 'streaming') {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMessage, id: Date.now().toString() }
                ]
              }
              return prev
            })
            // Clear current message ref AFTER updating messages
            currentMessageRef.current = ''
            // If conversation was created, notify parent
            if (data.conversation_id && onConversationCreated) {
              onConversationCreated(data.conversation_id)
            }
            // Force clear loading state multiple times to ensure it's cleared
            setTimeout(() => {
              setIsLoading(false)
              currentMessageRef.current = ''
            }, 0)
            setTimeout(() => {
              setIsLoading(false)
            }, 100)
          } else if (data.type === 'conversation_created') {
            // New conversation was created, update conversation ID
            if (onConversationCreated) {
              onConversationCreated(data.conversation_id)
            }
          } else if (data.type === 'error') {
            setIsLoading(false)
            currentMessageRef.current = ''
            setMessages(prev => [...prev, {
              id: Date.now().toString(),
              role: 'assistant',
              content: `Error: ${data.message || 'An error occurred'}`,
              timestamp: new Date()
            }])
          } else if (data.type === 'status') {
            if (data.status === 'processing') {
              setIsLoading(true)
            } else if (data.status === 'complete' || data.status === 'done') {
              setIsLoading(false)
            }
          }
        }
        
        websocket.onerror = (error) => {
          console.error('WebSocket error:', error)
          setWsConnected(false)
        }
        
        websocket.onclose = (event) => {
          console.log('WebSocket disconnected', event.code, event.reason)
          setWsConnected(false)
          setWs(null)
          wsRef.current = null
          isConnecting = false

          // Try to reconnect if not a normal closure
          if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++
            console.log(`Attempting to reconnect... (${reconnectAttempts}/${maxReconnectAttempts})`)
            reconnectTimeoutRef.current = setTimeout(() => {
              connectWebSocket()
            }, reconnectDelay * reconnectAttempts)
          }
        }
      } catch (error) {
        console.error('Failed to create WebSocket:', error)
        setWsConnected(false)
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket()
          }, reconnectDelay * reconnectAttempts)
        }
      }
    }

    connectWebSocket()
    
    return () => {
      shouldReconnect = false // Stop any reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
        wsRef.current.close()
        wsRef.current = null
      }
      setWs(null)
      setWsConnected(false)
    }
  }, []) // Remove conversationId dependency to prevent reconnections

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load conversation messages when conversation ID changes
  useEffect(() => {
    // Use environment variable for API URL with fallback
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    const loadConversation = async () => {
      if (conversationId) {
        try {
          const response = await fetch(`${API_URL}/api/chat/conversations/${conversationId}`)
          if (response.ok) {
            const data = await response.json()
            // Convert database messages to UI format
            const loadedMessages: Message[] = data.messages.map((msg: any) => ({
              id: msg.id.toString(),
              role: msg.role as 'user' | 'assistant',
              content: msg.content,
              timestamp: new Date(msg.created_at),
              attachments: msg.meta_data?.attachments || undefined
            }))
            setMessages(loadedMessages)
          }
        } catch (error) {
          console.error('Error loading conversation:', error)
        }
      } else {
        // New conversation - clear messages
        setMessages([])
        setInput('')
        currentMessageRef.current = ''
        setIsLoading(false)
      }
    }
    
    loadConversation()
  }, [conversationId])

  const handleSend = async () => {
    await handleSendWithAttachments()
  }

  // Clear chat when conversation changes
  useEffect(() => {
    if (conversationId === null && onNewConversation) {
      setMessages([])
    }
  }, [conversationId, onNewConversation])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Voice recording functionality
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'

        recognition.onresult = (event: any) => {
          let interimTranscript = ''
          let finalTranscript = ''

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript
            if (event.results[i].isFinal) {
              finalTranscript += transcript + ' '
            } else {
              interimTranscript += transcript
            }
          }

          if (voiceMode && finalTranscript.trim()) {
            // In voice mode, automatically send the message
            handleVoiceMessage(finalTranscript.trim())
          } else if (finalTranscript) {
            // In text mode, append to input
            setInput(prev => prev + finalTranscript)
          }
        }

        recognition.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error)
          setIsRecording(false)
          setIsListening(false)
        }

        recognition.onend = () => {
          setIsRecording(false)
          if (continuousListening) {
            // Restart listening if in continuous mode
            setTimeout(() => {
              if (continuousListening) {
                startListening()
              }
            }, 1000)
          } else {
            setIsListening(false)
          }
        }

        recognition.onstart = () => {
          setIsRecording(true)
          setIsListening(true)
        }

        recognitionRef.current = recognition
      }
    }
  }, [voiceMode, continuousListening])

  const startRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.start()
      setIsRecording(true)
    } else {
      alert('Speech recognition not supported in your browser')
    }
  }

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      setIsRecording(false)
    }
  }

  const startListening = () => {
    if (recognitionRef.current && !isRecording) {
      recognitionRef.current.start()
    }
  }

  const handleVoiceMessage = async (message: string) => {
    if (!message.trim() || isLoading || !ws) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    currentMessageRef.current = ''

    // Send message via WebSocket
    const sendMessage = () => {
      const currentWs = wsRef.current || ws
      if (currentWs && currentWs.readyState === WebSocket.OPEN) {
        currentWs.send(JSON.stringify({
          type: 'chat',
          message: message,
          conversation_id: conversationId,
          model: model
        }))
      }
    }

    sendMessage()
  }

  const toggleVoiceMode = () => {
    if (voiceMode) {
      // Switching off voice mode
      setVoiceMode(false)
      setContinuousListening(false)
      setIsListening(false)
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    } else {
      // Switching on voice mode
      setVoiceMode(true)
      setContinuousListening(true)
      startListening()
    }
  }

  // File upload handlers
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach(file => {
      const reader = new FileReader()
      reader.onload = (event) => {
        const attachment: Attachment = {
          id: Date.now().toString() + Math.random(),
          type: file.type.startsWith('image/') ? 'image' : 'file',
          name: file.name,
          url: event.target?.result as string,
          file: file
        }
        setAttachments(prev => [...prev, attachment])
      }
      reader.readAsDataURL(file)
    })
    if (e.target) e.target.value = ''
  }

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id))
  }

  const playTTS = async (text: string, messageId: string) => {
    if (playingAudio === messageId) {
      setPlayingAudio(null)
      return
    }

    try {
      setPlayingAudio(messageId)
      const response = await fetch('http://localhost:8000/api/chat/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'alloy' })
      })

      if (response.ok) {
        const audioBlob = await response.blob()
        const audioUrl = URL.createObjectURL(audioBlob)
        const audio = new Audio(audioUrl)
        audio.onended = () => setPlayingAudio(null)
        audio.play()
      } else if (response.status === 402) {
        // Quota exceeded
        alert('Voice output unavailable: OpenAI TTS quota exceeded. Text-to-speech is disabled.')
        setPlayingAudio(null)
      } else {
        alert('TTS failed: Service temporarily unavailable')
        setPlayingAudio(null)
      }
    } catch (error) {
      console.error('TTS error:', error)
      alert('TTS error: Service temporarily unavailable')
      setPlayingAudio(null)
    }
  }

  const enhanceImage = async (imageUrl: string, attachmentId: string, enhancementType: string = 'upscale') => {
    try {
      const response = await fetch('http://localhost:8000/api/chat/enhance-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_url: imageUrl, enhancement_type: enhancementType })
      })

      if (response.ok) {
        const data = await response.json()
        // Update the attachment with enhanced image
        setMessages(prev => prev.map(msg => ({
          ...msg,
          attachments: msg.attachments?.map(att =>
            att.id === attachmentId ? { ...att, url: data.enhanced_url } : att
          )
        })))
      } else {
        alert('Image enhancement failed')
      }
    } catch (error) {
      console.error('Enhancement error:', error)
      alert('Image enhancement error')
    }
  }

  const getEnhancementOptions = (imageUrl: string, attachmentId: string) => [
    { type: 'upscale', label: 'Upscale 2x', icon: '🔍' },
    { type: 'sharpen', label: 'Sharpen', icon: '✨' },
    { type: 'brighten', label: 'Brighten', icon: '☀️' },
    { type: 'hdr', label: 'HDR Effect', icon: '🌟' }
  ]

  const startEdit = (messageId: string, currentContent: string) => {
    setEditingMessageId(messageId)
    setEditedContent(currentContent)
  }

  const cancelEdit = () => {
    setEditingMessageId(null)
    setEditedContent('')
  }

  const saveEdit = async () => {
    if (!editingMessageId || !editedContent.trim()) return

    // Find the message being edited and its position
    const messageIndex = messages.findIndex(msg => msg.id === editingMessageId)
    if (messageIndex === -1) return

    const editedMessage = messages[messageIndex]

    // Update the message content
    const updatedMessages = [...messages]
    updatedMessages[messageIndex] = {
      ...editedMessage,
      content: editedContent.trim()
    }

    setMessages(updatedMessages)
    setEditingMessageId(null)
    setEditedContent('')

    // Remove all messages after the edited message (including AI responses)
    const messagesToKeep = updatedMessages.slice(0, messageIndex + 1)
    setMessages(messagesToKeep)

    // Regenerate AI response for the edited message and subsequent conversation
    setIsLoading(true)
    currentMessageRef.current = ''

    // Send the edited message and get new AI response
    const sendEditedMessage = () => {
      const currentWs = wsRef.current || ws
      if (currentWs && currentWs.readyState === WebSocket.OPEN) {
        currentWs.send(JSON.stringify({
          type: 'edit',
          message_id: editingMessageId,
          new_content: editedContent.trim(),
          conversation_id: conversationId,
          model: model
        }))
      }
    }

    sendEditedMessage()
  }

  const handleFileClick = () => {
    fileInputRef.current?.click()
  }

  const handleImageClick = () => {
    imageInputRef.current?.click()
  }

  // Update handleSend to include attachments
  const handleSendWithAttachments = async () => {
    if ((!input.trim() && attachments.length === 0) || isLoading || !ws) return

    // Upload attachments first if any
    let uploadedAttachments: Attachment[] = []
    if (attachments.length > 0) {
      setIsLoading(true)
      try {
        const formData = new FormData()
        attachments.forEach(att => {
          if (att.file) {
            formData.append('files', att.file)
          }
        })
        formData.append('conversation_id', conversationId?.toString() || '')

        const uploadResponse = await fetch('http://localhost:8000/api/chat/upload', {
          method: 'POST',
          body: formData
        })

        if (uploadResponse.ok) {
          const uploadData = await uploadResponse.json()
          uploadedAttachments = uploadData.files || []
        }
      } catch (error) {
        console.error('Error uploading files:', error)
        alert('Failed to upload files. Please try again.')
        setIsLoading(false)
        return
      }
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      attachments: uploadedAttachments.length > 0 ? uploadedAttachments : undefined
    }

    setMessages(prev => [...prev, userMessage])
    const messageToSend = input
    const messageWithAttachments = {
      message: messageToSend,
      attachments: uploadedAttachments.map(att => ({
        type: att.type,
        name: att.name,
        url: att.url
      }))
    }
    
    setInput('')
    setAttachments([])
    setIsLoading(true)
    currentMessageRef.current = ''

    // Send message via WebSocket - wait for connection if needed
    const sendMessage = () => {
      const currentWs = wsRef.current || ws
      if (currentWs && currentWs.readyState === WebSocket.OPEN) {
        currentWs.send(JSON.stringify({
          type: 'chat',
          ...messageWithAttachments,
          conversation_id: conversationId,
          model: model
        }))
        // Set a timeout to clear loading if no response in 30 seconds
        setTimeout(() => {
          if (isLoading) {
            setIsLoading(false)
            console.log('Loading timeout - clearing loading state')
          }
        }, 30000)
      } else if (currentWs && currentWs.readyState === WebSocket.CONNECTING) {
        // Wait for connection
        currentWs.addEventListener('open', () => {
          currentWs.send(JSON.stringify({
            type: 'chat',
            ...messageWithAttachments,
            conversation_id: conversationId,
            model: model
          }))
          // Set a timeout to clear loading if no response in 30 seconds
          setTimeout(() => {
            if (isLoading) {
              setIsLoading(false)
              console.log('Loading timeout - clearing loading state')
            }
          }, 30000)
        }, { once: true })
        // Also set a timeout for connection
        setTimeout(() => {
          if (currentWs.readyState === WebSocket.CONNECTING) {
            setIsLoading(false)
            console.log('Connection timeout - clearing loading state')
          }
        }, 5000)
      } else {
        setIsLoading(false)
        // Try to reconnect
        console.log('WebSocket not connected, attempting to reconnect...')
        // Check if backend is reachable
        fetch('http://localhost:8000/health')
          .then(() => {
            // Backend is up, WebSocket should reconnect automatically
            console.log('Backend is reachable, WebSocket will reconnect automatically')
          })
          .catch(() => {
            alert('Cannot connect to backend server. Please make sure the backend is running on port 8000.')
          })
      }
    }

    sendMessage()
  }

  return (
    <div className="flex flex-col h-screen max-h-screen overflow-hidden max-w-full mx-auto">
      {/* Messages Area - Fixed height with proper scrolling */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="h-full overflow-y-auto pt-10 pb-1 pl-1 pr-1 sm:pt-16 sm:pb-2 sm:pl-2 sm:pr-2 md:pt-20 md:pb-4 md:pl-4 md:pr-4 space-y-3 sm:space-y-4 scroll-smooth max-w-full">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center min-h-[400px]">
              <div className="relative mb-6">
                <Sparkles className="w-16 sm:w-20 h-16 sm:h-20 text-primary animate-pulse" />
                <div className="absolute inset-0 w-16 sm:w-20 h-16 sm:h-20 bg-primary/20 rounded-full blur-xl animate-ping"></div>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold mb-2 bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent px-4">
                Welcome to Advanced AI Agent
              </h2>
              <p className="text-muted-foreground mb-6 text-base sm:text-lg px-4 max-w-md">
                Unleash the power of AI. Voice commands, image enhancement, and limitless possibilities!
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 max-w-lg px-4">
                <div className="p-3 sm:p-4 bg-gradient-to-br from-secondary to-secondary/50 rounded-xl text-sm border border-primary/20 hover:border-primary/40 transition-all duration-300 hover:scale-105">
                  🎤 Voice Agent
                </div>
                <div className="p-3 sm:p-4 bg-gradient-to-br from-secondary to-secondary/50 rounded-xl text-sm border border-primary/20 hover:border-primary/40 transition-all duration-300 hover:scale-105">
                  🖼️ Image Enhancement
                </div>
                <div className="p-3 sm:p-4 bg-gradient-to-br from-secondary to-secondary/50 rounded-xl text-sm border border-primary/20 hover:border-primary/40 transition-all duration-300 hover:scale-105">
                  💻 Code Generation
                </div>
                <div className="p-3 sm:p-4 bg-gradient-to-br from-secondary to-secondary/50 rounded-xl text-sm border border-primary/20 hover:border-primary/40 transition-all duration-300 hover:scale-105">
                  🚀 Advanced Research
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} px-4 sm:px-4 md:px-6`}
            >
              <div
                className={`max-w-[70vw] sm:max-w-[75vw] md:max-w-[70vw] lg:max-w-[60vw] xl:max-w-[50vw] 2xl:max-w-[45vw] rounded-xl p-2 sm:p-3 md:p-4 relative shadow-lg border ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-primary to-purple-600 text-primary-foreground border-primary/50'
                    : 'bg-gradient-to-br from-secondary to-secondary/80 text-secondary-foreground border-border/50 backdrop-blur-sm'
                }`}
              >
                {message.role === 'user' && !editingMessageId && (
                  <button
                    onClick={() => startEdit(message.id, message.content)}
                    className="absolute top-2 right-2 p-1 rounded-full bg-accent hover:bg-accent/80 transition-colors z-10"
                    title="Edit message"
                  >
                    <Edit3 className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground" />
                  </button>
                )}
                {message.role === 'assistant' && message.content && (
                  <button
                    onClick={() => playTTS(message.content, message.id)}
                    className="absolute top-2 right-2 p-1 rounded-full bg-accent hover:bg-accent/80 transition-colors z-10"
                    title="Play audio"
                  >
                    <Volume2 className={`w-3 h-3 sm:w-4 sm:h-4 ${playingAudio === message.id ? 'text-red-500' : 'text-muted-foreground'}`} />
                  </button>
                )}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mb-2 space-y-2">
                    {message.attachments.map(att => (
                      <div key={att.id} className="relative">
                        {att.type === 'image' ? (
                          <div className="relative group">
                            <img
                              src={att.url}
                              alt={att.name}
                              className="max-w-full h-auto rounded-lg max-h-48 sm:max-h-64 object-contain"
                            />
                            <div className="absolute top-2 right-2 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              {getEnhancementOptions(att.url, att.id).map(option => (
                                <button
                                  key={option.type}
                                  onClick={() => enhanceImage(att.url, att.id, option.type)}
                                  className="p-1.5 sm:p-2 rounded-full bg-black/70 hover:bg-black/90 text-white transition-all duration-200 hover:scale-110"
                                  title={option.label}
                                >
                                  <span className="text-xs sm:text-sm">{option.icon}</span>
                                </button>
                              ))}
                            </div>
                            <div className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <div className="bg-black/70 text-white text-xs px-2 py-1 rounded">
                                Hover for enhancement
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2 p-2 bg-background/50 rounded">
                            <Paperclip className="w-3 h-3 sm:w-4 sm:h-4" />
                            <span className="text-xs sm:text-sm">{att.name}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {editingMessageId === message.id ? (
                  <div className="space-y-3">
                    <textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full min-h-[80px] p-3 border border-border/50 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary bg-background/90 backdrop-blur-sm text-sm sm:text-base"
                      placeholder="Edit your message..."
                      rows={3}
                    />
                    <div className="flex space-x-2 justify-end">
                      <button
                        onClick={cancelEdit}
                        className="px-3 py-1.5 text-sm bg-secondary hover:bg-secondary/80 rounded-lg transition-colors flex items-center space-x-1"
                      >
                        <XIcon className="w-4 h-4" />
                        <span>Cancel</span>
                      </button>
                      <button
                        onClick={saveEdit}
                        disabled={!editedContent.trim() || isLoading}
                        className="px-3 py-1.5 text-sm bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center space-x-1"
                      >
                        <Check className="w-4 h-4" />
                        <span>Save & Regenerate</span>
                      </button>
                    </div>
                  </div>
                ) : message.role === 'assistant' ? (
                  <div className="prose prose-xs sm:prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      className="text-sm sm:text-base"
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap text-sm sm:text-base">{message.content || (message.attachments && message.attachments.length > 0 ? '' : '')}</p>
                )}
              </div>
            </div>
          ))}

          {/* Only show loading spinner when actually waiting for response and no content is streaming */}
          {isLoading && currentMessageRef.current === '' && (
            <div className="flex justify-start px-2 sm:px-4">
              <div className="bg-secondary rounded-lg p-3 sm:p-4">
                <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="border-t border-border/50 bg-secondary/20 backdrop-blur-sm flex-shrink-0">
        <div className="p-3 sm:p-4">
          {/* Attachments preview */}
          {attachments.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2 max-w-4xl mx-auto">
              {attachments.map(att => (
                <div key={att.id} className="relative inline-block">
                  {att.type === 'image' ? (
                    <div className="relative">
                      <img
                        src={att.url}
                        alt={att.name}
                        className="w-16 h-16 sm:w-20 sm:h-20 object-cover rounded-lg"
                      />
                      <button
                        onClick={() => removeAttachment(att.id)}
                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center hover:bg-red-600"
                      >
                        <X className="w-3 h-3 sm:w-4 sm:h-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2 p-2 bg-secondary rounded-lg">
                      <Paperclip className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span className="text-xs sm:text-sm max-w-[80px] sm:max-w-[100px] truncate">{att.name}</span>
                      <button
                        onClick={() => removeAttachment(att.id)}
                        className="text-red-500 hover:text-red-600"
                      >
                        <X className="w-3 h-3 sm:w-4 sm:h-4" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="flex items-end space-x-2 max-w-4xl mx-auto">
            {/* File upload buttons */}
            <div className="flex space-x-1 flex-shrink-0">
              <button
                onClick={handleFileClick}
                className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                title="Attach file"
              >
                <Paperclip className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
              <button
                onClick={handleImageClick}
                className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                title="Attach image"
              >
                <ImageIcon className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.csv,.xlsx"
                onChange={handleFileSelect}
                className="hidden"
              />
              <input
                ref={imageInputRef}
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask anything... (Shift+Enter for new line)"
              className="flex-1 min-h-[50px] sm:min-h-[60px] max-h-[150px] sm:max-h-[200px] p-3 border border-border/50 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary bg-background/50 backdrop-blur-sm text-sm sm:text-base"
              rows={1}
            />

            {/* Voice recording button */}
            <button
              onClick={voiceMode ? toggleVoiceMode : (isRecording ? stopRecording : startRecording)}
              className={`p-2 sm:p-3 rounded-xl transition-all duration-300 flex-shrink-0 ${
                voiceMode
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg animate-pulse'
                  : isRecording
                  ? 'bg-red-500 text-white hover:bg-red-600'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
              }`}
              title={
                voiceMode
                  ? 'Disable voice conversation mode'
                  : isRecording
                  ? 'Stop recording'
                  : 'Start voice input'
              }
            >
              {voiceMode ? (
                <div className="flex items-center space-x-1">
                  <Mic className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="text-xs font-medium hidden sm:inline">VOICE</span>
                </div>
              ) : isRecording ? (
                <MicOff className="w-4 h-4 sm:w-5 sm:h-5" />
              ) : (
                <Mic className="w-4 h-4 sm:w-5 sm:h-5" />
              )}
            </button>

            <button
              onClick={handleSend}
              disabled={(!input.trim() && attachments.length === 0) || isLoading || !wsConnected}
              className="p-2 sm:p-3 bg-gradient-to-r from-primary to-purple-600 text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:scale-105 shadow-lg flex-shrink-0"
              title={!wsConnected ? 'Connecting to server...' : 'Send message'}
            >
              <Send className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          </div>
          {!wsConnected && (
            <div className="text-center text-xs text-yellow-600 dark:text-yellow-400 mt-2 max-w-4xl mx-auto">
              ⚠️ Connecting to server... Please wait
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
