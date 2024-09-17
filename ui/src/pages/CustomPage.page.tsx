import React from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { Center, Loader, TypographyStylesProvider } from '@mantine/core';
import { MarkdownPage } from '@/components/MarkdownPage';
import dataService, { useGetData } from '@/services/data.service';

export default () => {
  const { pageName } = useParams();
  const location = useLocation();

  const [data, isLoading, failed] = useGetData(
    async () => await dataService.getPage(pageName!),
    [pageName, location]
  );
  if (isLoading || !data || failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  switch (data.type) {
    case 'html':
      return (
        <TypographyStylesProvider>
          <div dangerouslySetInnerHTML={{ __html: data.content }} />
        </TypographyStylesProvider>
      );
    case 'markdown':
      return <MarkdownPage content={data.content} />;
  }
};
