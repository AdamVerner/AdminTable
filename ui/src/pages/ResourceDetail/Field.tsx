import React from 'react';
import { Grid } from '@mantine/core';
import DataField, { DataFieldProps } from '@/components/DataField';
import FieldTitle from '@/components/FieldTitle';

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
        <Grid.Col span={4}>
          <FieldTitle display={head.display} description={head.description} />
        </Grid.Col>
        <Grid.Col span="auto">
          <i>
            <DataField title={head.display} cell={field} />
          </i>
        </Grid.Col>
      </Grid>
    </div>
  );
};
