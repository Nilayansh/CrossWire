export function subscribeToTraceStream(
  incidentId: string,
  onEvent: (data: Record<string, unknown>) => void,
  onEnd?: () => void
): () => void {
  const eventSource = new EventSource(`/incidents/${encodeURIComponent(incidentId)}/stream`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
    } catch (e) {
      console.error('Failed to parse SSE event:', e);
    }
  };

  eventSource.addEventListener('end', () => {
    eventSource.close();
    onEnd?.();
  });

  eventSource.onerror = (err) => {
    console.warn('SSE stream closed or encountered error:', err);
    eventSource.close();
    onEnd?.();
  };

  return () => {
    eventSource.close();
  };
}
