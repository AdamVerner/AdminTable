import React from 'react';
import { Loader, Text, Title } from '@mantine/core';
import UserChart from '@/components/UserChart';
import dataService, { useGetData } from '@/services/data.service';

interface SubGraphProps {
  detail: {
    resource: string;
    detailId: string;
  };
  graph: {
    title: string;
    description: string;
    reference: string;
  };
}

export default function SubGraph({ detail, graph }: SubGraphProps) {
  const rangeFrom = null,
    rangeTo = null;

  const [data, isLoading, failed] = useGetData(async () => {
    return await dataService.getDetailGraph(
      detail.resource,
      detail.detailId,
      graph.reference,
      rangeFrom,
      rangeTo
    );
  }, [rangeFrom, rangeTo]);

  if (isLoading || !data || failed) {
    return (
      <div>
        <h4>{graph.title}</h4>
        {graph.description && <p>{graph.description}</p>}
        <Loader size="xl" />
      </div>
    );
  }

  const title = data.config?.title ?? graph.title;
  const description = data.config?.description ?? graph.description;
  return (
    <>
      <Title order={3}>{title}</Title>
      {description && <Text>{description}</Text>}
      <UserChart {...data} />
    </>
  );
}
