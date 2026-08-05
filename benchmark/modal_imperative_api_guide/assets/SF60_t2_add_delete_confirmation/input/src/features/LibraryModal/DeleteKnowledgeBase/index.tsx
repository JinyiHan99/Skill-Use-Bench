'use client';

import { Button } from '@lobehub/ui';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';

interface DeleteKnowledgeBaseProps {
  id: string;
  name: string;
  removeKnowledgeBase: (id: string) => Promise<void>;
  onDeleted?: () => void;
}

export const DeleteKnowledgeBase = memo<DeleteKnowledgeBaseProps>(
  ({ id, name, removeKnowledgeBase, onDeleted }) => {
    const { t } = useTranslation('knowledgeBase');

    const handleDelete = async () => {
      await removeKnowledgeBase(id);
      onDeleted?.();
    };

    return (
      <Button danger onClick={handleDelete} size="small" type="primary">
        {t('detail.delete')}: {name}
      </Button>
    );
  },
);

DeleteKnowledgeBase.displayName = 'DeleteKnowledgeBase';
