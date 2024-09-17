import React from 'react';
import { useParams } from 'react-router-dom';
import { Center, Loader, SimpleGrid, Stack, Title } from '@mantine/core';
import { Action } from '@/pages/ResourceDetail/Action';
import { Field } from '@/pages/ResourceDetail/Field';
import { SubTable } from '@/pages/ResourceDetail/SubTable';
import dataService, { useGetData } from '@/services/data.service';

export default () => {
  const { resourceName, detailId } = useParams();

  const [data, isLoading, failed] = useGetData(async () => {
    return await dataService.getDetail(resourceName!, detailId!);
  }, [resourceName, detailId]);

  if (isLoading || !data || failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return (
    <div>
      <Title order={1} mb="xl">
        {data.title}
      </Title>
      <SimpleGrid ml="md" cols={{ base: 1, md: 2, lg: 3 }}>
        {data.fields.map(([head, field], i) => (
          <Field key={i} head={head} field={field} />
        ))}
      </SimpleGrid>

      <Title order={2} mb="md" mt="xl">
        Actions
      </Title>
      <Stack ml="md">
        {data.actions.map((action, i) => (
          <Action key={i} action={action} />
        ))}
      </Stack>
      <Title order={2} mb="md" mt="xl">
        Tables
      </Title>
      <Stack ml="md">
        {data.tables.map((table, i) => (
          <SubTable key={i} table={table} />
        ))}
      </Stack>
      <Title order={2} mb="md" mt="xl">
        Graphs
      </Title>
      <div>TODO...</div>
      <Title order={2} mb="md" mt="xl">
        Live data
      </Title>
      <div>TODO...</div>
    </div>
  );
};
