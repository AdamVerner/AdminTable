import React from 'react';
import { AreaChart, BarChart, LineChart } from '@mantine/charts';
import { Loader, Text, Title } from '@mantine/core';
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
  let chart;
  switch (data.type) {
    case 'line':
      chart = <LineChart h={300} {...data.config} />;
      break;
    case 'bar':
      chart = <BarChart h={300} {...data.config} />;
      break;
    case 'area':
      chart = <AreaChart h={300} {...data.config} />;
      break;
    default:
      <Text c="red">Invalid chart type: {data.type}</Text>;
  }
  return (
    <>
      <Title order={3}>{title}</Title>
      {description && <Text>{description}</Text>}
      {chart}
    </>
  );
}
