'use client';

import { Button, Modal } from '@lobehub/ui';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const FeedbackForm = ({ onClose }: { onClose: () => void }) => {
  const { t } = useTranslation('common');

  return (
    <form>
      <textarea aria-label={t('feedback.placeholder')} rows={6} />
      <Button onClick={onClose} type="primary">
        {t('feedback.submit')}
      </Button>
    </form>
  );
};

export const FeedbackEntry = () => {
  const { t } = useTranslation('common');
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setOpen(true)}>{t('feedback.open')}</Button>
      <Modal
        footer={null}
        onCancel={() => setOpen(false)}
        open={open}
        styles={{ body: { padding: 0 } }}
        title={t('feedback.title')}
        width="min(90%, 640px)"
      >
        <FeedbackForm onClose={() => setOpen(false)} />
      </Modal>
    </>
  );
};
