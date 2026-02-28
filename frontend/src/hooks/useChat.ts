import { useCallback, useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import api from '../api/client';
import type { ChatMessage, ChatResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function useChat() {
  const { symbol, timeframe } = useSymbol();
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Reset conversation when symbol/timeframe changes
  useEffect(() => {
    setMessages([]);
  }, [symbol, timeframe]);

  const mutation = useMutation<ChatResponse, Error, string>({
    mutationFn: async (userMessage: string) => {
      const userMsg: ChatMessage = { role: 'user', content: userMessage };
      const allMessages = [...messages, userMsg];

      // Optimistically add user message
      setMessages(allMessages);

      const { data } = await api.post<ChatResponse>(
        `/api/interpretation/${symbol}/chat`,
        { messages: allMessages, timeframe },
      );

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response },
      ]);

      return data;
    },
  });

  const sendMessage = useCallback(
    (message: string) => mutation.mutate(message),
    [mutation],
  );

  const reset = useCallback(() => setMessages([]), []);

  return {
    messages,
    sendMessage,
    isLoading: mutation.isPending,
    reset,
  };
}
