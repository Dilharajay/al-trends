const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export async function fetchMetadata() {
  const res = await fetch(`${API_BASE}/metadata/options`);
  if (!res.ok) throw new Error(`Metadata request failed: ${res.statusText}`);
  return await res.json();
}

export async function predictCutoff(payload) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (res.status === 429) {
    const err = await res.json();
    throw new Error(err.detail || 'Rate limit exceeded. Please wait a moment.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Prediction failed');
  }
  return await res.json();
}

export async function evaluateStudent(payload) {
  const res = await fetch(`${API_BASE}/evaluate/student`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (res.status === 429) {
    const err = await res.json();
    throw new Error(err.detail || 'Rate limit exceeded. Please wait a moment.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Student evaluation failed');
  }
  return await res.json();
}

export async function predictBatch(items) {
  const res = await fetch(`${API_BASE}/predict/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  });
  if (res.status === 429) {
    const err = await res.json();
    throw new Error(err.detail || 'Rate limit exceeded. Please wait a moment.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Batch prediction failed');
  }
  return await res.json();
}
