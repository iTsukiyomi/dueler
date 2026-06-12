import { apiFetch } from './client';

export interface ChatMessage {
  role: 'user' | 'model';
  parts: { text: string }[];
}

export interface ChatResponse {
  text: string;
}

export interface LocalMessage {
  id: string;
  sender: 'user' | 'model';
  text: string;
  timestamp: number;
  suggestedTeam?: any;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: LocalMessage[];
  timestamp: number;
}

export interface SessionMessageResponse {
  userMessage: LocalMessage;
  botMessage: LocalMessage;
  sessionTitle: string;
}

export async function sendChatMessage(message: string, history?: ChatMessage[]): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history }),
  });
}

export async function fetchChatSessions(): Promise<ChatSession[]> {
  return apiFetch<ChatSession[]>('/api/chat/sessions');
}

export async function createChatSession(id?: string, title?: string, messages?: LocalMessage[]): Promise<ChatSession> {
  return apiFetch<ChatSession>('/api/chat/sessions', {
    method: 'POST',
    body: JSON.stringify({ id, title, messages }),
  });
}

export async function updateChatSession(id: string, updates: { title?: string; messages?: LocalMessage[] }): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/chat/sessions/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function sendSessionMessage(sessionId: string, message: string): Promise<SessionMessageResponse> {
  return apiFetch<SessionMessageResponse>(`/api/chat/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function deleteChatSession(sessionId: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/chat/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  });
}
