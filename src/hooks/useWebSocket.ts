'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

interface UseWebSocketReturn {
  isConnected: boolean
  subscribe: (channel: string) => void
  unsubscribe: (channel: string) => void
  sendMessage: (message: any) => void
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const socketRef = useRef<Socket | null>(null)
  const subscriptionsRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    // Initialize WebSocket connection
    socketRef.current = io(url, {
      transports: ['websocket'],
      autoConnect: true,
    })

    const socket = socketRef.current

    socket.on('connect', () => {
      setIsConnected(true)
      console.log('WebSocket connected')
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    })

    socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })

    // Handle market data updates
    socket.on('ticker', (data) => {
      // Handle ticker updates
      console.log('Ticker update:', data)
    })

    socket.on('depth', (data) => {
      // Handle order book updates
      console.log('Order book update:', data)
    })

    socket.on('trade', (data) => {
      // Handle trade updates
      console.log('Trade update:', data)
    })

    return () => {
      socket.disconnect()
    }
  }, [url])

  const subscribe = useCallback((channel: string) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('subscribe', { channel })
      subscriptionsRef.current.add(channel)
      console.log(`Subscribed to ${channel}`)
    }
  }, [isConnected])

  const unsubscribe = useCallback((channel: string) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('unsubscribe', { channel })
      subscriptionsRef.current.delete(channel)
      console.log(`Unsubscribed from ${channel}`)
    }
  }, [isConnected])

  const sendMessage = useCallback((message: any) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('message', message)
    }
  }, [isConnected])

  return {
    isConnected,
    subscribe,
    unsubscribe,
    sendMessage,
  }
}