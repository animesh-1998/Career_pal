import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use(config => {
  const stored = localStorage.getItem('careerpal_user');
  if (stored) {
    try {
      const user = JSON.parse(stored);
      if (user.token) config.headers.Authorization = `Bearer ${user.token}`;
    } catch {}
  }
  return config;
});

export const authAPI = {
  login: (email, password) =>
    api.post('/api/auth/login', { email, password }),
  signup: (name, email, password) =>
    api.post('/api/auth/signup', { name, email, password }),
};

export const chatAPI = {
  // Streaming chat — returns raw fetch Response
  sendMessage: async (message, threadId, onChunk) => {
    const stored = localStorage.getItem('careerpal_user');
    let token = null;
    if (stored) {
      try { token = JSON.parse(stored).token; } catch {}
    }

    const res = await fetch(`${BASE_URL}/api/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify({ message, thread_id: threadId }),
    });

    if (!res.ok) throw new Error('Chat request failed');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      const lines = text.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6);
          if (chunk) onChunk(chunk);
        }
      }
    }
  },

  // Upload file + message
  uploadAndChat: async (file, message, threadId, onChunk) => {
    const stored = localStorage.getItem('careerpal_user');
    let token = null;
    if (stored) {
      try { token = JSON.parse(stored).token; } catch {}
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', message);
    formData.append('thread_id', threadId);

    const res = await fetch(`${BASE_URL}/api/chat/upload`, {
      method: 'POST',
      headers: { ...(token && { Authorization: `Bearer ${token}` }) },
      body: formData,
    });

    if (!res.ok) throw new Error('Upload failed');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      const lines = text.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6);
          if (chunk) onChunk(chunk);
        }
      }
    }
  },

  approve: (threadId, decision) =>
    api.post('/api/chat/approve', { thread_id: threadId, decision }),
};

export default api;