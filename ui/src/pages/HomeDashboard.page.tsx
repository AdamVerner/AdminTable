import React from 'react';
import { Center, Loader } from '@mantine/core';
import { MarkdownPage } from '@/components/MarkdownPage';
import dataService, { useGetData } from '@/services/data.service';

export default () => {
  const [data, isLoading, failed] = useGetData(async () => await dataService.getDashboard(), []);
  if (isLoading || !data || failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return <MarkdownPage content={data.content} />;
};
