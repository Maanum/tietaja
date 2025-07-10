import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'error' | 'reply' | 'thoughts';
  content: string;
  timestamp: Date;
}

interface ChatProps {
  userId?: string;
}

const Chat: React.FC<ChatProps> = ({ userId = "kristofer" }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (type: 'user' | 'assistant' | 'error' | 'reply' | 'thoughts', content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;

    const userInput = inputValue.trim();
    setInputValue('');
    
    // Add user message
    addMessage('user', userInput);
    
    // Show loading state
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          user_input: userInput,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Add debug trace messages as a single thinking card (if any)
      if (data.debug_trace && Array.isArray(data.debug_trace) && data.debug_trace.length > 0) {
        const thoughtsContent = data.debug_trace.join('\n');
        addMessage('thoughts', thoughtsContent);
      }
      
      // Add assistant response
      addMessage('reply', data.response || data.message || 'No response received');
      
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage('error', `Failed to send message. Please try again. Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessageContent = (message: Message) => {
    if (message.type === 'reply') {
      return (
        <ReactMarkdown 
          className="prose prose-sm max-w-none"
          components={{
            // Custom styling for markdown elements
            h1: ({children}) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
            h2: ({children}) => <h2 className="text-base font-semibold mb-2">{children}</h2>,
            h3: ({children}) => <h3 className="text-sm font-semibold mb-1">{children}</h3>,
            p: ({children}) => <p className="mb-2">{children}</p>,
            ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
            ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
            li: ({children}) => <li className="text-sm">{children}</li>,
            strong: ({children}) => <strong className="font-semibold">{children}</strong>,
            em: ({children}) => <em className="italic">{children}</em>,
            code: ({children}) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
            a: ({href, children}) => (
              <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            ),
            blockquote: ({children}) => (
              <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600">
                {children}
              </blockquote>
            ),
          }}
        >
          {message.content}
        </ReactMarkdown>
      );
    }
    
    // For user, error, and thoughts messages, render as plain text
    return <div className="text-sm whitespace-pre-wrap">{message.content}</div>;
  };

  const getMessageStyle = (message: Message) => {
    switch (message.type) {
      case 'user':
        return 'bg-blue-500 text-white';
      case 'error':
        return 'bg-red-100 text-red-800 border border-red-200';
      case 'thoughts':
        return 'bg-gray-100 text-gray-700 border border-gray-200 font-mono text-xs';
      case 'reply':
        return 'bg-white text-gray-800 border border-gray-200';
      default:
        return 'bg-white text-gray-800 border border-gray-200';
    }
  };

  const getMessageAlignment = (message: Message) => {
    switch (message.type) {
      case 'user':
        return 'justify-end';
      case 'thoughts':
        return 'justify-start';
      default:
        return 'justify-start';
    }
  };

  const getTimeStyle = (message: Message) => {
    switch (message.type) {
      case 'user':
        return 'text-blue-100';
      case 'error':
        return 'text-red-600';
      case 'thoughts':
        return 'hidden'; // Hide timestamp for thoughts
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-800">Tietäjä</h1>
        <p className="text-sm text-gray-600">AI Assistant</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p>Start a conversation with Tietäjä</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${getMessageAlignment(message)}`}
          >
            <div
              className={`max-w-xs lg:max-w-2xl px-4 py-3 rounded-lg shadow-sm ${getMessageStyle(message)}`}
            >
              {renderMessageContent(message)}
              <div className={`text-xs mt-2 ${getTimeStyle(message)}`}>
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-800 border border-gray-200 px-4 py-3 rounded-lg shadow-sm">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span className="text-sm">Tietäjä is thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat; 