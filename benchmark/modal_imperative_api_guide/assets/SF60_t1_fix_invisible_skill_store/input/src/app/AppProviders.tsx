'use client';

import { AntdRegistry } from '@ant-design/nextjs-registry';
import { App, ModalHost as RootModalHost, ThemeProvider } from '@lobehub/ui';
import { PropsWithChildren } from 'react';

export const AppProviders = ({ children }: PropsWithChildren) => {
  return (
    <AntdRegistry>
      <ThemeProvider>
        <App>
          <RootModalHost />
          {children}
        </App>
      </ThemeProvider>
    </AntdRegistry>
  );
};
