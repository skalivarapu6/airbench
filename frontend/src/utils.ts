export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    queued: '#6c7086',
    running: '#f9e2af',
    completed: '#a6e3a1',
    failed: '#f38ba8',
    cancelled: '#89dceb',
  };
  return colors[status] || '#cdd6f4';
};
