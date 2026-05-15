import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

test('renders app navigation', () => {
  const queryClient = new QueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  );

  const linkElement = screen.getByRole('link', { name: /^articles$/i });
  expect(linkElement).toBeInTheDocument();
});
