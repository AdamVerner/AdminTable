import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Center, Loader, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import Description from '@/components/Description';
import { Action } from '@/pages/ResourceDetail/Action';
import { Field } from '@/pages/ResourceDetail/Field';
import SubGraph from '@/pages/ResourceDetail/SubGraph';
import { SubTable } from '@/pages/ResourceDetail/SubTable';
import dataService, { useGetData } from '@/services/data.service';

export default () => {
  const { resourceName, detailId } = useParams();
  const navigate = useNavigate();
  const [refresh, setRefresh] = React.useState(1);
  const [data, isLoading, failed] = useGetData(async () => {
    return await dataService.getDetail(resourceName!, detailId!);
  }, [resourceName, detailId, refresh]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (failed.includes('Resource not found: ')) {
        navigate(-1);
      }
    }, 5000);
    return () => clearTimeout(timeout);
  }, [failed]);

  if (failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Stack>
          <Title order={2} mb="md" mt="xl">
            Loading resource failed:
          </Title>
          <Text>{failed}</Text>
        </Stack>
      </Center>
    );
  }

  if (isLoading || !data) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return (
    <div style={{ width: '100%', overflow: 'hidden' }}>
      <Title mb="xs" order={1}>
        {data.title}
      </Title>
      <Description description={data.description} />
      <SimpleGrid ml="md" cols={{ base: 1, md: 2, lg: 3 }}>
        {data.fields.map(([head, field], i) => (
          <Field key={i} head={head} field={field} />
        ))}
      </SimpleGrid>

      {data.actions.length > 0 && (
        <>
          <Title order={2} mb="md" mt="xl">
            Actions
          </Title>
          <Stack ml="md">
            {data.actions.map((action, i) => (
              <Action key={i} action={action} onRefresh={() => setRefresh(refresh + 1)} />
            ))}
          </Stack>
        </>
      )}
      {data.tables.length > 0 && (
        <>
          <Title order={2} mb="md" mt="xl">
            Tables
          </Title>
          <Stack ml="md">
            {data.tables.map((table, i) => (
              <SubTable key={i} table={table} />
            ))}
          </Stack>
        </>
      )}
      {data.graphs.length > 0 && (
        <>
          <Title order={2} mb="md" mt="xl">
            Graphs
          </Title>
          <Stack ml="md">
            {data.graphs.map((graph, i) => (
              <SubGraph
                key={i}
                detail={{ resource: resourceName!, detailId: detailId as string }}
                graph={graph}
              />
            ))}
          </Stack>
        </>
      )}
      <Title order={2} mb="md" mt="xl">
        Live data
      </Title>
      <div>TODO...</div>
    </div>
  );
};
