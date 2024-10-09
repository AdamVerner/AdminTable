import React, { PropsWithChildren } from 'react';
import { Group, Tooltip } from '@mantine/core';
import { fix_title } from '@/components/DataField';

interface FieldTitleProps {
  display: string;
  description?: string;
}

export default ({ display, description, children }: PropsWithChildren<FieldTitleProps>) => {
  return (
    <Group>
      {description ? (
        <Tooltip label={description}>
          <span>{fix_title(display)}</span>
        </Tooltip>
      ) : (
        <span>{fix_title(display)}</span>
      )}
      {children}
    </Group>
  );
};
