import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App, registerModules } from '@chit/core';
import '@chit/core/styles';

// Every submodule's web/index.ts self-registers by dropping a file here: no central list to edit,
// so parallel module branches do not conflict.
registerModules(
  import.meta.glob('../../../modules/*/submodules/*/web/index.ts', { eager: true, import: 'default' }),
);

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: true, staleTime: 30_000 } },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
