'use client';

import { Button } from '@lobehub/ui';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';

import { useCreateNewModal } from '@/features/LibraryModal/CreateNew';

interface QuickCreatePanelProps {
  onCreated?: (id: string) => void;
}

export const QuickCreatePanel = memo<QuickCreatePanelProps>(({ onCreated }) => {
  const { t } = useTranslation('knowledgeBase');
  const { open } = useCreateNewModal();

  return (
    <section>
      <h3>{t('createNew.title')}</h3>
      <p>{t('createNew.description')}</p>
      <Button onClick={() => open({ onSuccess: onCreated })} type="primary">
        {t('createNew.action')}
      </Button>
    </section>
  );
});

QuickCreatePanel.displayName = 'QuickCreatePanel';
