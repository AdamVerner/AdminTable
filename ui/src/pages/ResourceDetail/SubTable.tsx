import React, { useState } from 'react';
import { Loader, Table, Title } from '@mantine/core';
import PageSelect from '@/pages/ResourceList/PageSelect';
import TableBody from '@/pages/ResourceList/TableBody';
import TableHead from '@/pages/ResourceList/TableHead';
import dataService, { useGetData } from '@/services/data.service';

interface SubTableProps {
  table: {
    title: string;
    description: string;
    resource: string;
    filter: {
      col: string;
      op: string;
      val: string;
    };
  };
}

export const SubTable = ({ table }: SubTableProps) => {
  const [{ page, perPage }, setPagination] = useState({ page: 1, perPage: 10 });
  const [data, isLoading, failed] = useGetData(async () => {
    return await dataService.getTable(table.resource, {
      page,
      perPage,
      sort: null,
      filters: [
        {
          ref: table.filter.col,
          op: table.filter.op,
          val: table.filter.val,
        },
      ],
    });
  }, [table, page, perPage]);

  if (isLoading || !data || failed) {
    return <Loader size="xl" />;
  }

  return (
    <div>
      <Title order={3}>{table.title}</Title>
      {table.description && <p>{table.description}</p>}
      <Table striped>
        <TableHead header={data.header} />
        <TableBody rows={data.data} />
      </Table>
      <PageSelect
        page={data.pagination.page}
        perPage={data.pagination.per_page}
        total={data.pagination.total}
        setPage={(page) => setPagination({ page, perPage })}
        setPerPage={(perPage) => setPagination({ page: 1, perPage })}
        float={false}
      />
    </div>
  );
};
