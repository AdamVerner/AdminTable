import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { Button, Center, Group, Loader, Table, Title } from '@mantine/core';
import Description from '@/components/Description';
import PageSelect from '@/pages/ResourceList/PageSelect';
import TableBody from '@/pages/ResourceList/TableBody';
import TableHead from '@/pages/ResourceList/TableHead';
import { useTableParams } from '@/pages/ResourceList/utils';
import dataService, { useGetData } from '@/services/data.service';
import FilterSelection from './FilterSelection';

export default () => {
  const { state: SearchState, setPerPage, setPage, setSort } = useTableParams();
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
    <div style={{ width: '100%' }}>
      <Group mb="xs">
        <Title order={1}>{data.meta.title}</Title>
        {data.meta.has_create && (
          <Button component={Link} to={`/resource/${resourceName}/create`}>
            Create New
          </Button>
        )}
      </Group>

      <Description description={data.meta.description} />
      <FilterSelection
        applied_filters={data.applied_filters}
        available_filters={data.available_filters}
      />
      <Table striped>
        <TableHead header={data.header} setSort={setSort} />
        <TableBody header={data.header} rows={data.data} />
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
