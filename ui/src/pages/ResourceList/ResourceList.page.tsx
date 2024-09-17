import React from 'react';
import Markdown from 'react-markdown';
import { Link, useParams } from 'react-router-dom';
import remarkGfm from 'remark-gfm';
import { Button, Center, Group, Loader, Table, TypographyStylesProvider } from '@mantine/core';
import PageSelect from '@/pages/ResourceList/PageSelect';
import TableBody from '@/pages/ResourceList/TableBody';
import TableHead from '@/pages/ResourceList/TableHead';
import { useTableParams } from '@/pages/ResourceList/utils';
import dataService, { useGetData } from '@/services/data.service';
import FilterSelection from './FilterSelection';

export default () => {
  const { state: SearchState, setPerPage, setPage } = useTableParams();
  const { resourceName } = useParams();

  const [data, isLoading, failed] = useGetData(async () => {
    return await dataService.getTable(resourceName!, {
      page: SearchState?.page ?? 1,
      perPage: SearchState?.perPage ?? 50,
      sort: SearchState?.sort ?? null,
      filters: SearchState?.filters ?? [],
    });
  }, [resourceName, JSON.stringify(SearchState)]);

  if (isLoading || !data || failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return (
    <div>
      <Group>
        <h1>{data.meta.title}</h1>
        {data.meta.has_create && (
          <Button component={Link} to={`/resource/${resourceName}/create`}>
            Create New
          </Button>
        )}
      </Group>

      {data.meta.description && (
        <TypographyStylesProvider>
          <Markdown>{data.meta.description}</Markdown>
        </TypographyStylesProvider>
      )}
      <FilterSelection
        applied_filters={data.applied_filters}
        available_filters={data.available_filters}
      />
      <Table striped>
        <TableHead header={data.header} />
        <TableBody rows={data.data} />
      </Table>
      <PageSelect
        page={data.pagination.page}
        perPage={data.pagination.per_page}
        total={data.pagination.total}
        setPage={setPage}
        setPerPage={setPerPage}
      />
    </div>
  );
};
