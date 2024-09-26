import React from 'react';
import { Grid, Tooltip } from '@mantine/core';
import DataField, { DataFieldProps } from '@/components/DataField';

export const Field = ({
  head,
  field,
}: {
  head: {
    ref: string;
    display: string;
    sortable: boolean;
    description: string;
  };
  field: DataFieldProps['cell'];
}) => {
  return (
    <div>
      <Grid>
        {head.description ? (
          <Tooltip label={head.description}>
            <Grid.Col span={4}>{head.display}:</Grid.Col>
          </Tooltip>
        ) : (
          <Grid.Col span={4}>{head.display}:</Grid.Col>
        )}
        <Grid.Col span="auto">
          <i>
            <DataField title={head.display} cell={field} />
          </i>
        </Grid.Col>
      </Grid>
    </div>
  );
};
